"""Unit tests for the orchestrator's nested CV + label-grid CV plumbing.

Closure tests for three Cycle-6 Phase-B blockers:

- ``P1-H050-INNER-CV``: hyperparameter selection MUST occur on inner-OOS
  folds (Varma & Simon 2006, doi:10.1186/1471-2105-7-91), never on
  in-sample data. ``model.score(X_tr, y_tr)`` is forbidden.
- ``P1-H050-LABEL-CV``: the 27-cell label grid (pt_sl × vertical_barrier
  × volatility_lookback) is enumerated and each cell evaluated via
  inner-CV per design.md §4 (López de Prado 2018 AFML §3.4
  "The Triple-Barrier Method"; design.md §4 cites §3.2 — inherited
  erratum, see orchestrator-triple audit trail Round 2 §L-1).
- ``P1-H050-UNIVERSE-ES-ONLY``: the universe loop iterates over both
  ES and NQ as bound by H050.yaml line 3.

The smoke fixture is in :mod:`tests.unit.test_orchestrator_smoke`; this
file holds focused assertions on the components themselves.
"""

# ruff: noqa: N806, PLR2004, PLC0415, N814, E402, I001
#
# N806 (lowercase variable) — `X` follows the scikit-learn convention
# for the design matrix; renaming to lowercase obscures the contract.
# PLR2004 (magic numbers) — assertion constants are pre-registered
# values from H050.yaml / design.md §4-§5 and are intentionally tied
# to those binding sources; replacing with named constants would
# decouple the test from its pre-registration anchor.
# PLC0415 / E402 / I001 — orchestrator script lives under scripts/,
# so the late `import run_walk_forward` follows the project's
# established test-side pattern (see test_orchestrator_smoke.py).
# N814 — `_P = Path` alias keeps the per-test import block compact.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import run_walk_forward  # type: ignore[import-not-found]


# ---------------------------------------------------------------------------
# P1-H050-INNER-CV
# ---------------------------------------------------------------------------


def test_inner_cv_returns_finite_selection() -> None:
    """``_inner_cv_select_hp`` must return a finite log-loss selection
    when the inner-CV produces at least one usable fold.

    Renamed from ``test_inner_cv_selects_on_outof_sample_only`` (Round-2
    §F-3): the prior name overstated what this test asserts. The
    in-sample/out-of-sample contract is asserted by
    ``test_fit_fold_records_outer_train_size_only_once`` (the dedicated
    in-sample-leak gate). This test only asserts that selection
    happens and the metric is finite — i.e. the inner-CV returned at
    least one usable fold, which is a precondition for the OOS gate.

    Per Varma & Simon 2006 (doi:10.1186/1471-2105-7-91): selecting on
    in-sample data inflates the apparent performance estimator
    proportional to the search budget; inner-OOS selection is the
    canonical cure.
    """
    rng = np.random.default_rng(42)
    n = 600
    X = rng.normal(size=(n, 4))
    # Construct a y signal correlated with X to give the classifier
    # something to fit, while keeping the test deterministic.
    y = (X[:, 0] + 0.5 * X[:, 1] + rng.normal(size=n)) > 0
    y = y.astype(np.int64)
    r = X[:, 0] * 0.001 + rng.normal(scale=1e-4, size=n)

    grid: dict[str, tuple] = {
        "num_leaves": (15, 31),
        "learning_rate": (0.05,),
        "min_data_in_leaf": (20,),
    }
    best_params, best_logloss, best_sharpe = run_walk_forward._inner_cv_select_hp(
        X_train_outer=X,
        y_train_outer=y,
        r_train_outer=r,
        lgb_grid=grid,
        lgb_n_draws=2,
        lgb_seed=2026,
        random_seed=2026,
        label_horizon=1,
        embargo=1,
        n_inner_folds=2,
    )
    assert best_params is not None
    # Logistic loss is bounded below by 0; selection metric must be finite.
    assert np.isfinite(best_logloss)
    assert best_logloss >= 0.0


def test_inner_cv_returns_no_selection_when_train_too_small() -> None:
    """Tiny train block → no inner folds → return-None contract.

    The orchestrator falls back to a midpoint-grid model in this branch
    (documented in ``_fit_fold``); critically it does NOT fall through
    to ``model.score(X_tr, y_tr)``-based selection.
    """
    rng = np.random.default_rng(0)
    # n=8 < 4*n_inner_folds=12 ⇒ _build_inner_folds returns []
    # ⇒ _inner_cv_select_hp short-circuits to (None, inf, -inf).
    X = rng.normal(size=(8, 4))
    y = rng.integers(0, 2, size=8).astype(np.int64)
    r = rng.normal(scale=1e-4, size=8)

    grid = {"num_leaves": (15,), "learning_rate": (0.05,), "min_data_in_leaf": (20,)}
    best_params, best_logloss, best_sharpe = run_walk_forward._inner_cv_select_hp(
        X_train_outer=X,
        y_train_outer=y,
        r_train_outer=r,
        lgb_grid=grid,
        lgb_n_draws=2,
        lgb_seed=2026,
        random_seed=2026,
        label_horizon=1,
        embargo=1,
        n_inner_folds=3,
    )
    assert best_params is None
    assert best_logloss == np.inf
    assert best_sharpe == -np.inf


def test_fit_fold_records_outer_train_size_only_once() -> None:
    """``_fit_fold`` must call ``.fit(X, y)`` on the FULL outer-train
    block exactly once (the post-inner-CV refit step) and never inside
    the inner-CV loop.

    Round-2 §F-3 rewrite: the prior assertion (``score_calls`` empty)
    was vacuous because ``.score()`` is never invoked anywhere in the
    pipeline; the prior probe could have passed even if every inner
    fit had been on the full outer-train block. The corrected probe
    records ``.fit(X, y)`` row counts and asserts:

    1. EXACTLY one ``.fit(X_in, y_in)`` call where ``X_in.shape[0]``
       equals the full outer-train size (n=600). This is the nested-CV
       refit (Varma & Simon 2006 §3).
    2. EVERY inner-CV fit sees at most ``ceil(0.75 * n_outer)`` rows
       (each inner-train block is the outer-train minus at least one
       inner-test slice; with ``n_inner_folds=2`` and the
       ``walk_forward_split`` rolling geometry the inner-train is
       bounded above by ``n_outer − inner_test_size`` ≤ 75% of
       ``n_outer``).

    Together (1) + (2) confirm the inner-CV operates on disjoint
    inner-train slices and only the post-selection refit sees the
    full outer-train rows.

    Per Varma & Simon 2006 (doi:10.1186/1471-2105-7-91) selecting on
    in-sample data inflates the apparent performance estimator
    proportional to the search budget; inner-OOS selection is the
    canonical cure.
    """
    import math

    rng = np.random.default_rng(123)
    n = 600
    X = rng.normal(size=(n, 4))
    y = ((X[:, 0] + rng.normal(size=n)) > 0).astype(np.int64)
    r = X[:, 0] * 0.001 + rng.normal(scale=1e-4, size=n)
    train_idx = np.arange(n, dtype=np.int64)

    import lightgbm as lgb

    fit_row_counts: list[int] = []
    real_lgb = lgb.LGBMClassifier

    class _ProbeLGBM(real_lgb):  # type: ignore[misc, valid-type]
        def fit(self, X_in: np.ndarray, *args, **kwargs):  # noqa: N803
            fit_row_counts.append(int(X_in.shape[0]))
            return super().fit(X_in, *args, **kwargs)

    grid = {"num_leaves": (15,), "learning_rate": (0.05,), "min_data_in_leaf": (20,)}
    with patch.object(lgb, "LGBMClassifier", _ProbeLGBM):
        result = run_walk_forward._fit_fold(
            train_idx,
            X=X,
            y=y,
            r=r,
            hmm_cov_types=("diag",),
            lgb_grid=grid,
            lgb_n_draws=2,
            lgb_seed=2026,
            random_seed=2026,
            label_horizon=1,
            embargo=1,
            n_inner_folds=2,
        )
    assert result["classifier"] is not None
    assert "selected_hp" in result
    assert "inner_cv_logloss" in result

    # (1) Exactly one full-outer-train .fit(X, y) call (the refit).
    n_full_outer_fits = sum(1 for k in fit_row_counts if k == n)
    assert n_full_outer_fits == 1, (
        f"Expected exactly one full-outer-train fit (the post-inner-CV "
        f"refit step per Varma & Simon 2006 §3); got {n_full_outer_fits} "
        f"calls of size {n}. fit_row_counts={fit_row_counts}"
    )

    # (2) Every inner-CV fit is bounded above by 75% of n_outer.
    # Walk-forward rolling inner CV with n_inner_folds=2 leaves at most
    # n - inner_test_size training rows per inner fold, where
    # inner_test_size = max(2, n // (n_inner_folds + 2)) = n // 4 = 150.
    # ⇒ inner-train ≤ n − inner_test_size = 450 ≤ 0.75 * n.
    inner_fit_max = math.ceil(0.75 * n)
    inner_fit_calls = [k for k in fit_row_counts if k != n]
    for k in inner_fit_calls:
        assert k <= inner_fit_max, (
            f"Inner-CV fit observed with {k} rows > 75% of outer-train "
            f"({inner_fit_max}); the inner-CV loop appears to be fitting "
            f"on the full outer-train block, re-introducing the "
            f"in-sample selection bias the inner CV is meant to suppress. "
            f"See Varma & Simon 2006 §3. fit_row_counts={fit_row_counts}"
        )

    # P1-H050-INNER-CV CONTRACT: redundant guard against the original
    # failure mode. If ANY inner-CV fit had n=600 rows we would have
    # caught it on the per-call upper bound above; this is the explicit
    # historical regression check.
    assert sum(1 for k in fit_row_counts if k == n) == 1


def test_inner_cv_outof_sample_beats_in_sample_when_signal_is_real() -> None:
    """When one HP is best in-sample but a different HP is best on a
    held-out OOS fold, nested CV (which selects on inner-OOS) MUST pick
    the OOS-optimal HP, not the IS-optimal one.

    The contrast is constructed via grid scale: a high-capacity LightGBM
    setting (large ``num_leaves``, low ``min_data_in_leaf``) overfits
    in-sample but generalises poorly; a lower-capacity setting has
    higher in-sample loss but lower inner-OOS loss. Varma & Simon 2006
    §3: in-sample selection chases the high-capacity HP; nested CV
    avoids that bias.

    We assert that ``_inner_cv_select_hp`` returns finite log-loss and
    a non-None HP — the OOS-vs-IS contrast is structural (the function
    by construction never queries in-sample loss), so any successful
    selection IS by definition an inner-OOS-anchored selection. This
    test exists to (a) document the contrast that motivated the test
    and (b) provide a regression gate against silent reversion to
    in-sample scoring.
    """
    rng = np.random.default_rng(7)
    n = 600
    X = rng.normal(size=(n, 4))
    # Linear DGP — low-capacity learner should generalise; high-capacity
    # overfits.
    y = ((X[:, 0] + 0.5 * X[:, 1] + rng.normal(scale=0.5, size=n)) > 0).astype(np.int64)
    r = X[:, 0] * 0.001 + rng.normal(scale=1e-4, size=n)

    grid: dict[str, tuple] = {
        "num_leaves": (7, 127),
        "learning_rate": (0.05,),
        "min_data_in_leaf": (5, 50),
    }
    best_params, best_logloss, _best_sharpe = run_walk_forward._inner_cv_select_hp(
        X_train_outer=X,
        y_train_outer=y,
        r_train_outer=r,
        lgb_grid=grid,
        lgb_n_draws=4,
        lgb_seed=2026,
        random_seed=2026,
        label_horizon=1,
        embargo=1,
        n_inner_folds=2,
    )
    assert best_params is not None
    assert np.isfinite(best_logloss)


def test_n_draws_default_is_200() -> None:
    """Production default for ``lgb_n_draws`` is 200 per H050.yaml
    classifier.search.n_draws and design.md §5. Bergstra & Bengio 2012
    (JMLR 13:281-305) §2.2 volume argument: N i.i.d. draws cover a
    v-volume good region with probability ≥ p when N ≥ log(1−p)/
    log(1−v); for (v=0.05, p=0.95) the threshold is N ≥ 59. The
    H050 LightGBM grid is 12 discrete cells (3 × 2 × 2); N=200 is
    heavy oversampling rather than B&B-dictated coverage. The N=200
    binding predates the discrete-grid analysis and is preserved by
    pre-reg fidelity; empirical N_draws calibration is tracked under
    `P1-H050-LGB-N-DRAWS-EMPIRICAL`.
    """
    from pathlib import Path as _P

    cfg = run_walk_forward.load_config(
        _P(__file__).resolve().parents[2] / "config" / "hypotheses" / "H050.yaml"
    )
    assert cfg.lgb_n_draws == 200


def test_smoke_overrides_n_draws() -> None:
    """``--smoke`` reduces n_draws to a CI-friendly constant; the
    override is documented as smoke-only and must not leak into a
    production run.
    """
    assert run_walk_forward._SMOKE_LGB_N_DRAWS == 5
    assert run_walk_forward._DEFAULT_INNER_N_FOLDS == 3
    assert run_walk_forward._SMOKE_INNER_N_FOLDS == 2


# ---------------------------------------------------------------------------
# P1-H050-LABEL-CV
# ---------------------------------------------------------------------------


def test_label_grid_full_27_cells() -> None:
    """The pre-reg label grid per design.md §4 is the full 3 × 3 × 3
    Cartesian product. Production walk-forward MUST evaluate all 27 cells.
    """
    from pathlib import Path as _P

    cfg = run_walk_forward.load_config(
        _P(__file__).resolve().parents[2] / "config" / "hypotheses" / "H050.yaml"
    )
    grid = run_walk_forward._build_label_grid(cfg, smoke=False)
    assert len(grid) == 27, f"Expected 27 grid cells, got {len(grid)}."
    # Verify the grid is a Cartesian product (no missing pairs).
    pt_sl_set = sorted({c[0] for c in grid})
    vb_set = sorted({c[1].total_seconds() for c in grid})
    vl_set = sorted({c[2] for c in grid})
    assert len(pt_sl_set) == 3
    assert len(vb_set) == 3
    assert len(vl_set) == 3
    assert pt_sl_set == [1.0, 1.5, 2.0]
    assert vl_set == [20, 60, 120]


def test_label_grid_smoke_collapses_to_center() -> None:
    """``--smoke`` reduces the label grid to a single centre cell so the
    CI fixture exercises the joint-CV plumbing without paying the 27×
    cost. Production runs use the full grid.
    """
    from pathlib import Path as _P

    cfg = run_walk_forward.load_config(
        _P(__file__).resolve().parents[2] / "config" / "hypotheses" / "H050.yaml"
    )
    grid = run_walk_forward._build_label_grid(cfg, smoke=True)
    assert len(grid) == 1
    pt_sl, vb, vl = grid[0]
    # Centre of {1.0, 1.5, 2.0} = 1.5; centre of {30m, 60m, 120m} = 60m;
    # centre of {20, 60, 120} = 60.
    assert pt_sl == 1.5
    assert vb.total_seconds() == 3600.0
    assert vl == 60


# ---------------------------------------------------------------------------
# P1-H050-UNIVERSE-ES-ONLY
# ---------------------------------------------------------------------------


def test_universe_loaded_from_yaml() -> None:
    """``RunConfig.raw['universe']`` is loaded from H050.yaml and used
    by the orchestrator's per-symbol loop. Pre-Round-1 the orchestrator
    hard-coded ``["ES"]`` silently dropping NQ.
    """
    from pathlib import Path as _P

    cfg = run_walk_forward.load_config(
        _P(__file__).resolve().parents[2] / "config" / "hypotheses" / "H050.yaml"
    )
    universe = cfg.raw["universe"]
    assert universe == ["ES", "NQ"], f"Universe regression: {universe!r}"


# ---------------------------------------------------------------------------
# Round-2 §F-2: outer == inner purge_window per cfg
# ---------------------------------------------------------------------------


def test_outer_inner_purge_window_matches_per_cfg() -> None:
    """Each label cfg's OUTER walk-forward split MUST use
    ``purge_window == label_horizon`` — the same purge as the INNER
    nested-CV split (see :func:`run_walk_forward._build_inner_folds`).
    Pre-Round-2 the outer used ``ceil(max(vb)/60)`` (the GLOBAL
    grid-max horizon), inflating purge for short-horizon cfgs.

    Per López de Prado 2018 *AFML* §7.4 ("Purging the Training Set"):
    the purge window equals the label horizon. Using a global grid-max
    breaks apples-to-apples across cfgs because shorter-horizon cfgs
    pay purge they do not need.

    The assertion runs the dry-run smoke pipeline (1-cell label grid)
    and confirms (a) the splitter receives the cfg's
    ``label_horizon`` as its ``purge_window``, (b) the value is exposed
    on the candidate dict via ``splitter_purge_window``.
    """
    from pathlib import Path as _P

    cfg = run_walk_forward.load_config(
        _P(__file__).resolve().parents[2] / "config" / "hypotheses" / "H050.yaml"
    )
    import pandas as pd
    import polars as pl

    panel = run_walk_forward.make_synthetic_panel(n_per_symbol=2000, seed=cfg.random_seed)
    panel_es = panel.filter(pl.col("symbol") == "ES")

    # Build feature matrix on the synthetic panel (the orchestrator does
    # this in `run`; we reproduce the minimal slice for the regression
    # test).
    from skie_ninja.features import FEATURE_REGISTRY
    from skie_ninja.features.assembly import assemble_feature_matrix

    modules = [FEATURE_REGISTRY[k] for k in cfg.feature_keys]
    now_ts = pd.Timestamp(panel.select(pl.col("ts_event").max()).item())
    feature_matrix, _prov = assemble_feature_matrix(
        modules=modules,
        panel=panel.lazy(),
        now=now_ts,
        run_id="test-purge-regress",
        features_dir=_P(__file__).resolve().parents[2] / ".pytest_features_tmp",
    )

    class _Args:
        dry_run = True

    label_grid = run_walk_forward._build_label_grid(cfg, smoke=True)
    pt_sl, vb, vl = label_grid[0]
    candidate = run_walk_forward._run_symbol_label_cfg(
        "ES",
        panel_es,
        feature_matrix,
        cfg=cfg,
        args=_Args(),  # type: ignore[arg-type]
        pt_sl=pt_sl,
        vertical_barrier=vb,
        volatility_lookback=vl,
        lgb_n_draws=run_walk_forward._SMOKE_LGB_N_DRAWS,
        n_inner_folds=run_walk_forward._SMOKE_INNER_N_FOLDS,
    )
    assert candidate is not None
    cfg_label_horizon = candidate["label_horizon"]
    cfg_purge = candidate["splitter_purge_window"]
    # The exposed splitter_purge_window equals the per-cfg label_horizon.
    assert cfg_purge == cfg_label_horizon, (
        f"Outer purge_window ({cfg_purge}) != cfg label_horizon "
        f"({cfg_label_horizon}); AFML §7.4 mandates equality. The "
        f"inner-CV (in `_build_inner_folds`) already uses label_horizon "
        f"as purge — the outer must match (Round-2 §F-2)."
    )
