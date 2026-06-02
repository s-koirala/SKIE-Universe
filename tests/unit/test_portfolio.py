"""Unit tests for the simultaneous multi-asset long/short portfolio engine (ADR-0020).

`src/skie_ninja/meta/portfolio.py` — union independent per-asset signals →
joint-Kelly long/short sizing → per-instrument gross caps → book return stream.
Deterministic RNG seeds.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.meta.portfolio import (
    PortfolioResult,
    cap_by_instrument,
    construct_portfolio,
    directional_returns,
)

_SEED = 20260602


class TestDirectionalReturns:
    def test_long_passes_through(self) -> None:
        s = np.array([[1.0, 1.0]])
        r = np.array([[0.02, -0.01]])
        np.testing.assert_array_equal(directional_returns(s, r), r)

    def test_short_negates(self) -> None:
        s = np.array([[-1.0]])
        r = np.array([[0.02]])
        assert directional_returns(s, r)[0, 0] == pytest.approx(-0.02)

    def test_flat_is_zero(self) -> None:
        s = np.array([[0.0]])
        r = np.array([[0.05]])
        assert directional_returns(s, r)[0, 0] == 0.0

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="shape mismatch"):
            directional_returns(np.ones((10, 2)), np.ones((10, 3)))

    def test_not_2d_raises(self) -> None:
        with pytest.raises(ValueError, match="must be 2-D"):
            directional_returns(np.ones(10), np.ones(10))

    def test_continuous_signal_scales(self) -> None:
        s = np.array([[0.5, -0.5]])
        r = np.array([[0.02, 0.04]])
        out = directional_returns(s, r)
        assert out[0, 0] == pytest.approx(0.01)  # 0.5 * 0.02
        assert out[0, 1] == pytest.approx(-0.02)  # -0.5 * 0.04


class TestCapByInstrument:
    def test_float_cap_binds_proportionally(self) -> None:
        f = np.array([0.4, 0.4, 0.3])  # ES bets gross 0.8; NQ bet gross 0.3
        capped, gross, bound = cap_by_instrument(f, ["ES", "ES", "NQ"], 0.5)
        assert bound
        assert gross["ES"] == pytest.approx(0.5)  # 0.8 throttled to 0.5
        assert gross["NQ"] == pytest.approx(0.3)  # under cap, unchanged
        assert capped[0] == pytest.approx(0.4 * 0.5 / 0.8)  # proportional throttle

    def test_dict_cap_missing_key_uncapped(self) -> None:
        f = np.array([0.6, 0.4])
        capped, gross, bound = cap_by_instrument(f, ["ES", "NQ"], {"ES": 0.5})
        assert bound
        assert gross["ES"] == pytest.approx(0.5)
        assert gross["NQ"] == pytest.approx(0.4)  # no cap key → uncapped

    def test_no_bind_when_under_cap(self) -> None:
        f = np.array([0.2, 0.2])
        _, gross, bound = cap_by_instrument(f, ["ES", "NQ"], 0.5)
        assert not bound
        assert gross["ES"] == pytest.approx(0.2)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="instrument_ids length"):
            cap_by_instrument(np.array([0.1, 0.2]), ["ES"], 0.5)

    def test_nonpositive_cap_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            cap_by_instrument(np.array([0.1]), ["ES"], 0.0)

    def test_int_cap_treated_as_uniform_scalar(self) -> None:
        # CR-1 audit regression: an int cap must be a uniform scalar, not crash via .get().
        f = np.array([0.6, 0.3])
        _, gross, bound = cap_by_instrument(f, ["ES", "ES"], 5)
        assert not bound  # gross 0.9 < int cap 5
        assert gross["ES"] == pytest.approx(0.9)


class TestConstructPortfolio:
    def test_long_and_short_both_allocated_bad_bet_zeroed(self) -> None:
        rng = np.random.default_rng(_SEED)
        n = 300
        rising = rng.normal(0.01, 0.03, n)
        falling = rng.normal(-0.01, 0.03, n)
        # bet 0: long the riser (good); bet 1: short the faller (good); bet 2: long the faller (bad)
        signals = np.column_stack([np.ones(n), -np.ones(n), np.ones(n)])
        asset_rets = np.column_stack([rising, falling, falling])
        result = construct_portfolio(
            directional_returns(signals, asset_rets), total_exposure_cap=2.0
        )
        assert isinstance(result, PortfolioResult)
        assert result.fractions[0] > 0.0  # long riser
        assert result.fractions[1] > 0.0  # short faller (profitable short → allocated)
        assert result.fractions[2] == pytest.approx(0.0, abs=1e-3)  # long faller → no allocation

    def test_total_within_cap(self) -> None:
        rng = np.random.default_rng(_SEED)
        dr = rng.normal(0.02, 0.03, size=(300, 3))
        result = construct_portfolio(dr, total_exposure_cap=0.5)
        assert result.gross_exposure <= 0.5 + 1e-6

    def test_portfolio_returns_equal_matrix_times_fractions(self) -> None:
        rng = np.random.default_rng(_SEED)
        dr = rng.normal(0.005, 0.04, size=(300, 4))
        result = construct_portfolio(dr, total_exposure_cap=1.0)
        np.testing.assert_allclose(result.portfolio_returns, dr @ result.fractions)
        assert np.isfinite(result.growth_rate)

    def test_instrument_cap_integrated(self) -> None:
        rng = np.random.default_rng(_SEED)
        dr = rng.normal(0.02, 0.03, size=(300, 3))  # strong edge → fractions push to caps
        result = construct_portfolio(
            dr,
            total_exposure_cap=3.0,
            instrument_ids=["ES", "ES", "NQ"],
            per_instrument_cap=0.2,
        )
        assert result.per_instrument_gross["ES"] <= 0.2 + 1e-6
        assert result.per_instrument_gross["NQ"] <= 0.2 + 1e-6

    def test_instrument_ids_without_cap_raises(self) -> None:
        with pytest.raises(ValueError, match="per_instrument_cap is required"):
            construct_portfolio(np.zeros((10, 2)), instrument_ids=["ES", "NQ"])

    def test_not_2d_raises(self) -> None:
        with pytest.raises(ValueError, match="must be 2-D"):
            construct_portfolio(np.zeros(10))

    def test_single_bet_book(self) -> None:
        rng = np.random.default_rng(_SEED)
        dr = rng.normal(0.01, 0.04, size=(300, 1))
        result = construct_portfolio(dr, total_exposure_cap=1.0)
        assert result.n_bets == 1
        assert result.portfolio_returns.shape == (300,)

    def test_instrument_capped_flag_and_empty_gross(self) -> None:
        rng = np.random.default_rng(_SEED)
        dr = rng.normal(0.02, 0.03, size=(300, 2))
        capped = construct_portfolio(
            dr, total_exposure_cap=3.0, instrument_ids=["ES", "ES"], per_instrument_cap=0.1
        )
        assert capped.instrument_capped is True
        uncapped = construct_portfolio(dr, total_exposure_cap=0.05)
        assert uncapped.instrument_capped is False
        assert uncapped.per_instrument_gross == {}  # no instrument_ids → empty

    def test_growth_rate_analytic_constant(self) -> None:
        # constant directional return r → book return = r·gross; growth = log(1 + r·gross).
        dr = np.full((300, 2), 0.01)
        result = construct_portfolio(dr, total_exposure_cap=0.5)
        assert result.growth_rate == pytest.approx(
            np.log(1.0 + 0.01 * result.gross_exposure), rel=1e-6
        )

    def test_n_periods_and_status_fields(self) -> None:
        rng = np.random.default_rng(_SEED)
        dr = rng.normal(0.01, 0.04, size=(250, 3))
        result = construct_portfolio(dr, total_exposure_cap=1.0)
        assert result.n_periods == 250
        assert result.converged is True
        assert result.bankrupts_on_path is False

    def test_shared_instrument_long_short_gross_capped(self) -> None:
        rng = np.random.default_rng(_SEED)
        n = 300
        rising = rng.normal(0.01, 0.03, n)
        falling = rng.normal(-0.01, 0.03, n)
        # two profitable ES bets sharing one instrument budget: long ES-rising + short ES-falling.
        signals = np.column_stack([np.ones(n), -np.ones(n)])
        asset_rets = np.column_stack([rising, falling])
        result = construct_portfolio(
            directional_returns(signals, asset_rets),
            total_exposure_cap=3.0,
            instrument_ids=["ES", "ES"],
            per_instrument_cap=0.3,
        )
        assert result.fractions[0] > 0.0  # long rising
        assert result.fractions[1] > 0.0  # short falling
        assert result.per_instrument_gross["ES"] <= 0.3 + 1e-6  # gross-capped across both
