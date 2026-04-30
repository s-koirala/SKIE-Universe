"""Regression tests for src/skie_ninja/backtest/lgb_inner_cv_checkpoint.py.

Mirrors the structure + coverage shape of test_cfg_checkpoint.py: round-
trip round-tripping, schema-version gate, atomic-write cleanup,
provenance drift, discover semantics, merge resume.

Schema v2 (2026-04-30, Round-1 audit R-1-1 fix): cache key extended to
(cfg_signature, fold_id, draw_idx). Q-1-1 fix: discover_draws +
merge_resume_into_current return sorted dicts. Q-1-2 fix: lgb_seed
in cfg subdirectory name.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pytest

from skie_ninja.backtest import cfg_checkpoint as _cfg_checkpoint
from skie_ninja.backtest import lgb_inner_cv_checkpoint as _lgb


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    d = tmp_path / "run123"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def cfg_signature() -> str:
    # 64-char hex (SHA256 of canonical "NQ|12|1.5000000000|1800|120")
    return _lgb.cfg_signature_from_key_tuple(("NQ", 12, 1.5, 1800, 120))


@pytest.fixture
def sample_params() -> dict:
    return {
        "num_leaves": 31,
        "max_depth": 7,
        "learning_rate": 0.05,
        "min_child_samples": 20,
    }


# -----------------------------------------------------------------------
# Round-trip
# -----------------------------------------------------------------------


def test_save_then_load_round_trip(run_dir: Path, cfg_signature: str, sample_params: dict) -> None:
    fold_loglosses = [0.6932, 0.6845, 0.6901]
    fold_sharpes = [0.31, -0.12, 0.55]

    path = _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=3,
        draw_idx=42,
        params=sample_params,
        fold_loglosses=fold_loglosses,
        fold_sharpes=fold_sharpes,
        producing_run_id="abcd1234",
        lgb_seed=2026,
    )
    assert path.exists()
    assert path.name == "fold_03_draw_0042.pkl"

    payload = _lgb.load_draw_checkpoint(path)
    assert payload["schema_version"] == _lgb.SCHEMA_VERSION
    assert payload["fold_id"] == 3
    assert payload["draw_idx"] == 42
    assert payload["params"] == sample_params
    assert payload["fold_loglosses"] == fold_loglosses
    assert payload["fold_sharpes"] == fold_sharpes
    assert payload["producing_run_id"] == "abcd1234"
    assert payload["cfg_signature"] == cfg_signature
    assert payload["lgb_seed"] == 2026


def test_atomic_write_no_tmp_leftover(run_dir: Path, cfg_signature: str, sample_params: dict) -> None:
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.5],
        fold_sharpes=[0.1],
        producing_run_id=None,
    )
    cfg_dir = _lgb.lgb_inner_cv_cfg_dir(run_dir, cfg_signature)
    leftovers = list(cfg_dir.glob("*.tmp"))
    assert leftovers == []


def test_load_schema_version_mismatch_raises(run_dir: Path, cfg_signature: str) -> None:
    cfg_dir = _lgb.lgb_inner_cv_cfg_dir(run_dir, cfg_signature)
    cfg_dir.mkdir(parents=True)
    bad = cfg_dir / "fold_00_draw_0001.pkl"
    with bad.open("wb") as f:
        pickle.dump({"schema_version": "v1_legacy"}, f, protocol=5)
    with pytest.raises(ValueError, match="schema-version mismatch"):
        _lgb.load_draw_checkpoint(bad)


# -----------------------------------------------------------------------
# discover_draws (returns dict[(fold_id, draw_idx), payload])
# -----------------------------------------------------------------------


def test_discover_draws_empty_dir(run_dir: Path, cfg_signature: str) -> None:
    out = _lgb.discover_draws(run_dir, cfg_signature)
    assert out == {}


def test_discover_draws_skips_non_pickle_files(
    run_dir: Path, cfg_signature: str, sample_params: dict
) -> None:
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=5,
        params=sample_params,
        fold_loglosses=[0.69],
        fold_sharpes=[0.0],
        producing_run_id=None,
    )
    cfg_dir = _lgb.lgb_inner_cv_cfg_dir(run_dir, cfg_signature)
    (cfg_dir / "README.txt").write_text("ignore me")
    (cfg_dir / "fold_xx_draw_yyyy.pkl").write_text("malformed")  # name doesn't match regex
    (cfg_dir / "draw_0001.pkl").write_text("v1 legacy filename")  # also rejected

    out = _lgb.discover_draws(run_dir, cfg_signature)
    assert set(out.keys()) == {(0, 5)}


def test_discover_draws_skips_corrupt_pickle(
    run_dir: Path, cfg_signature: str
) -> None:
    cfg_dir = _lgb.lgb_inner_cv_cfg_dir(run_dir, cfg_signature)
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "fold_00_draw_0001.pkl").write_bytes(b"\x80\x05not-a-pickle-payload")
    out = _lgb.discover_draws(run_dir, cfg_signature)
    assert out == {}


def test_discover_draws_returns_multiple_indexed(
    run_dir: Path, cfg_signature: str, sample_params: dict
) -> None:
    for f, d in [(0, 0), (0, 1), (1, 0), (2, 7), (3, 199)]:
        _lgb.save_draw_checkpoint(
            run_dir=run_dir,
            cfg_signature=cfg_signature,
            fold_id=f,
            draw_idx=d,
            params=sample_params,
            fold_loglosses=[0.69],
            fold_sharpes=[0.0],
            producing_run_id=None,
        )
    out = _lgb.discover_draws(run_dir, cfg_signature)
    assert set(out.keys()) == {(0, 0), (0, 1), (1, 0), (2, 7), (3, 199)}


def test_discover_draws_returns_sorted(
    run_dir: Path, cfg_signature: str, sample_params: dict
) -> None:
    """Q-1-1 fix: dict is sorted by (fold_id, draw_idx)."""
    # Save in non-monotonic order
    for f, d in [(2, 5), (0, 1), (1, 0), (0, 0)]:
        _lgb.save_draw_checkpoint(
            run_dir=run_dir,
            cfg_signature=cfg_signature,
            fold_id=f,
            draw_idx=d,
            params=sample_params,
            fold_loglosses=[0.69],
            fold_sharpes=[0.0],
            producing_run_id=None,
        )
    out = _lgb.discover_draws(run_dir, cfg_signature)
    keys = list(out.keys())
    assert keys == sorted(keys), f"discover_draws must return sorted dict; got {keys}"


# -----------------------------------------------------------------------
# Fold-collision prevention (R-1-1 critical fix)
# -----------------------------------------------------------------------


def test_fold_id_in_key_prevents_overwrite(
    run_dir: Path, cfg_signature: str, sample_params: dict
) -> None:
    """R-1-1 critical: fold_id must be part of the cache key.
    Without fold_id, fold 1's save would overwrite fold 0's."""
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.5],  # fold 0 logloss
        fold_sharpes=[0.1],
        producing_run_id="r1",
    )
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=1,
        draw_idx=0,  # SAME draw_idx, different fold
        params=sample_params,
        fold_loglosses=[0.7],  # fold 1 logloss (would overwrite under v1)
        fold_sharpes=[0.2],
        producing_run_id="r1",
    )
    out = _lgb.discover_draws(run_dir, cfg_signature)
    assert (0, 0) in out
    assert (1, 0) in out
    assert out[(0, 0)]["fold_loglosses"] == [0.5]
    assert out[(1, 0)]["fold_loglosses"] == [0.7]


def test_filter_draws_by_fold(sample_params: dict) -> None:
    cached = {
        (0, 0): {"fold_id": 0, "draw_idx": 0, "fold_loglosses": [0.5]},
        (0, 1): {"fold_id": 0, "draw_idx": 1, "fold_loglosses": [0.6]},
        (1, 0): {"fold_id": 1, "draw_idx": 0, "fold_loglosses": [0.7]},
        (2, 0): {"fold_id": 2, "draw_idx": 0, "fold_loglosses": [0.8]},
    }
    fold0 = _lgb.filter_draws_by_fold(cached, fold_id=0)
    assert set(fold0.keys()) == {0, 1}
    fold1 = _lgb.filter_draws_by_fold(cached, fold_id=1)
    assert set(fold1.keys()) == {0}
    assert fold1[0]["fold_loglosses"] == [0.7]
    fold99 = _lgb.filter_draws_by_fold(cached, fold_id=99)
    assert fold99 == {}


# -----------------------------------------------------------------------
# lgb_seed isolation (Q-1-2 fix)
# -----------------------------------------------------------------------


def test_lgb_seed_in_cfg_dir_path(run_dir: Path, cfg_signature: str) -> None:
    """Q-1-2 fix: cfg subdirectory name includes lgb_seed when provided,
    so cross-seed runs cannot share pickles."""
    dir_no_seed = _lgb.lgb_inner_cv_cfg_dir(run_dir, cfg_signature)
    dir_seed_a = _lgb.lgb_inner_cv_cfg_dir(run_dir, cfg_signature, lgb_seed=2026)
    dir_seed_b = _lgb.lgb_inner_cv_cfg_dir(run_dir, cfg_signature, lgb_seed=2027)
    assert dir_seed_a != dir_seed_b
    assert dir_seed_a != dir_no_seed
    assert "seed_2026" in str(dir_seed_a)
    assert "seed_2027" in str(dir_seed_b)


def test_cross_seed_isolation(
    run_dir: Path, cfg_signature: str, sample_params: dict
) -> None:
    """A run with lgb_seed=2026 and a run with lgb_seed=2027 do NOT
    share pickles — each has its own subdirectory."""
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.5],
        fold_sharpes=[0.1],
        producing_run_id=None,
        lgb_seed=2026,
    )
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,  # same fold + draw_idx
        params=sample_params,
        fold_loglosses=[0.9],  # different params under different seed
        fold_sharpes=[0.5],
        producing_run_id=None,
        lgb_seed=2027,
    )
    found_2026 = _lgb.discover_draws(run_dir, cfg_signature, lgb_seed=2026)
    found_2027 = _lgb.discover_draws(run_dir, cfg_signature, lgb_seed=2027)
    assert found_2026[(0, 0)]["fold_loglosses"] == [0.5]
    assert found_2027[(0, 0)]["fold_loglosses"] == [0.9]


# -----------------------------------------------------------------------
# cfg_signature_from_key_tuple
# -----------------------------------------------------------------------


def test_cfg_signature_matches_cfg_checkpoint_canonical_format() -> None:
    key = _cfg_checkpoint.CfgKey(
        sym="NQ", cfg_idx=12, pt_sl=1.5, vertical_barrier_seconds=1800, volatility_lookback=120
    )
    sig_via_cfg = key.signature()
    sig_via_lgb = _lgb.cfg_signature_from_key_tuple(("NQ", 12, 1.5, 1800, 120))
    assert sig_via_cfg == sig_via_lgb


def test_cfg_signature_stable_across_repeated_call() -> None:
    sig_a = _lgb.cfg_signature_from_key_tuple(("ES", 1, 1.0, 1800, 20))
    sig_b = _lgb.cfg_signature_from_key_tuple(("ES", 1, 1.0, 1800, 20))
    assert sig_a == sig_b


def test_cfg_signature_distinct_for_distinct_keys() -> None:
    sig_a = _lgb.cfg_signature_from_key_tuple(("ES", 1, 1.0, 1800, 20))
    sig_b = _lgb.cfg_signature_from_key_tuple(("NQ", 1, 1.0, 1800, 20))
    sig_c = _lgb.cfg_signature_from_key_tuple(("ES", 2, 1.0, 1800, 20))
    assert sig_a != sig_b
    assert sig_a != sig_c


# -----------------------------------------------------------------------
# merge_resume_into_current
# -----------------------------------------------------------------------


def test_merge_resume_current_overrides_prior(
    tmp_path: Path, cfg_signature: str, sample_params: dict
) -> None:
    prior_run = tmp_path / "prior"
    cur_run = tmp_path / "current"
    prior_run.mkdir()
    cur_run.mkdir()

    _lgb.save_draw_checkpoint(
        run_dir=prior_run,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.99],
        fold_sharpes=[0.0],
        producing_run_id="prior",
    )
    _lgb.save_draw_checkpoint(
        run_dir=cur_run,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.50],
        fold_sharpes=[0.1],
        producing_run_id="current",
    )
    _lgb.save_draw_checkpoint(
        run_dir=cur_run,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=1,
        params=sample_params,
        fold_loglosses=[0.55],
        fold_sharpes=[0.2],
        producing_run_id="current",
    )

    merged = _lgb.merge_resume_into_current(
        prior_run_dir=prior_run, current_run_dir=cur_run, cfg_signature=cfg_signature
    )
    assert set(merged.keys()) == {(0, 0), (0, 1)}
    assert merged[(0, 0)]["fold_loglosses"] == [0.50]
    assert merged[(0, 0)]["producing_run_id"] == "current"


def test_merge_resume_no_prior_run_dir(
    run_dir: Path, cfg_signature: str, sample_params: dict
) -> None:
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.5],
        fold_sharpes=[0.0],
        producing_run_id=None,
    )
    merged = _lgb.merge_resume_into_current(
        prior_run_dir=None, current_run_dir=run_dir, cfg_signature=cfg_signature
    )
    assert set(merged.keys()) == {(0, 0)}


def test_merge_resume_no_current_dir(
    tmp_path: Path, cfg_signature: str, sample_params: dict
) -> None:
    prior = tmp_path / "prior"
    cur = tmp_path / "current"
    prior.mkdir()
    cur.mkdir()
    _lgb.save_draw_checkpoint(
        run_dir=prior,
        cfg_signature=cfg_signature,
        fold_id=2,
        draw_idx=3,
        params=sample_params,
        fold_loglosses=[0.5],
        fold_sharpes=[0.0],
        producing_run_id="prior",
    )
    merged = _lgb.merge_resume_into_current(
        prior_run_dir=prior, current_run_dir=cur, cfg_signature=cfg_signature
    )
    assert set(merged.keys()) == {(2, 3)}


def test_merge_resume_prior_with_no_cfg_subdir(
    tmp_path: Path, cfg_signature: str, sample_params: dict
) -> None:
    """R-1-5 fix: prior_run_dir exists but contains no cfg subdir
    (e.g. prior crashed before reaching this cfg)."""
    prior = tmp_path / "prior"
    cur = tmp_path / "current"
    prior.mkdir()  # exists but no _lgb_inner_cv_checkpoints/
    cur.mkdir()
    _lgb.save_draw_checkpoint(
        run_dir=cur,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.5],
        fold_sharpes=[0.0],
        producing_run_id="cur",
    )
    merged = _lgb.merge_resume_into_current(
        prior_run_dir=prior, current_run_dir=cur, cfg_signature=cfg_signature
    )
    assert set(merged.keys()) == {(0, 0)}


def test_merge_resume_returns_sorted_dict(
    tmp_path: Path, cfg_signature: str, sample_params: dict
) -> None:
    """Q-1-1 fix: merge_resume_into_current returns sorted dict."""
    cur = tmp_path / "cur"
    cur.mkdir()
    for f, d in [(2, 5), (0, 1), (1, 0), (0, 0)]:
        _lgb.save_draw_checkpoint(
            run_dir=cur,
            cfg_signature=cfg_signature,
            fold_id=f,
            draw_idx=d,
            params=sample_params,
            fold_loglosses=[0.5],
            fold_sharpes=[0.0],
            producing_run_id=None,
        )
    merged = _lgb.merge_resume_into_current(
        prior_run_dir=None, current_run_dir=cur, cfg_signature=cfg_signature
    )
    keys = list(merged.keys())
    assert keys == sorted(keys)


# -----------------------------------------------------------------------
# is_complete
# -----------------------------------------------------------------------


def test_is_complete_full_coverage() -> None:
    n_draws = 5
    n_outer_folds = 3
    cached = {
        (f, d): {} for f in range(n_outer_folds) for d in range(n_draws)
    }
    assert _lgb.is_complete(cached, n_draws=n_draws, n_outer_folds=n_outer_folds) is True


def test_is_complete_partial_coverage() -> None:
    cached = {(0, 0): {}, (0, 1): {}, (1, 0): {}}
    assert _lgb.is_complete(cached, n_draws=5, n_outer_folds=3) is False


def test_is_complete_empty() -> None:
    assert _lgb.is_complete({}, n_draws=1, n_outer_folds=1) is False


# -----------------------------------------------------------------------
# check_provenance
# -----------------------------------------------------------------------


def test_provenance_no_drift_under_same_env(
    run_dir: Path, cfg_signature: str, sample_params: dict
) -> None:
    _lgb.save_draw_checkpoint(
        run_dir=run_dir,
        cfg_signature=cfg_signature,
        fold_id=0,
        draw_idx=0,
        params=sample_params,
        fold_loglosses=[0.5],
        fold_sharpes=[0.0],
        producing_run_id=None,
    )
    payload = next(iter(_lgb.discover_draws(run_dir, cfg_signature).values()))
    mismatches = _lgb.check_provenance(payload)
    assert mismatches == []


def test_provenance_python_version_drift(sample_params: dict) -> None:
    payload = {
        "schema_version": _lgb.SCHEMA_VERSION,
        "git_head": "deadbeef",
        "python_version": "3.7.0",
        "numpy_version": np.__version__,
        "fold_id": 0,
        "draw_idx": 0,
        "params": sample_params,
        "fold_loglosses": [0.5],
        "fold_sharpes": [0.0],
    }
    mismatches = _lgb.check_provenance(payload)
    assert any("python_version mismatch" in m for m in mismatches)


def test_provenance_numpy_version_drift(sample_params: dict) -> None:
    import platform as _p
    payload = {
        "schema_version": _lgb.SCHEMA_VERSION,
        "git_head": "deadbeef",
        "python_version": _p.python_version(),
        "numpy_version": "0.0.0-fake",
        "fold_id": 0,
        "draw_idx": 0,
        "params": sample_params,
        "fold_loglosses": [0.5],
        "fold_sharpes": [0.0],
    }
    mismatches = _lgb.check_provenance(payload)
    assert any("numpy_version mismatch" in m for m in mismatches)


def test_provenance_git_head_drift(sample_params: dict) -> None:
    import platform as _p
    payload = {
        "schema_version": _lgb.SCHEMA_VERSION,
        "git_head": "deadbeef" * 5,
        "python_version": _p.python_version(),
        "numpy_version": np.__version__,
        "fold_id": 0,
        "draw_idx": 0,
        "params": sample_params,
        "fold_loglosses": [0.5],
        "fold_sharpes": [0.0],
    }
    mismatches = _lgb.check_provenance(payload, current_git_head="cafef00d" * 5)
    assert any("git_head mismatch" in m for m in mismatches)


# -----------------------------------------------------------------------
# write_resume_telemetry (post-fold-projection input)
# -----------------------------------------------------------------------


def test_write_resume_telemetry_shape() -> None:
    cached_for_fold = {0: {}, 5: {}}
    record = _lgb.write_resume_telemetry(
        sym="NQ",
        cfg_idx=12,
        cfg_signature="abcdef0123456789" + "0" * 48,
        fold_id=2,
        n_draws=200,
        cached_for_fold=cached_for_fold,
        provenance_drift_count=1,
    )
    assert record["module"] == "lgb_inner_cv_checkpoint"
    assert record["sym"] == "NQ"
    assert record["cfg_idx"] == 12
    assert record["fold_id"] == 2
    assert record["n_draws_total"] == 200
    assert record["n_draws_cached"] == 2
    assert record["n_draws_remaining"] == 198
    assert record["provenance_drift_count"] == 1
    assert record["cfg_signature_short"] == "abcdef0123456789"


# -----------------------------------------------------------------------
# Filename / path helpers
# -----------------------------------------------------------------------


def test_filename_has_zero_pad() -> None:
    key = _lgb.LgbDrawKey(cfg_signature="abc" * 22, fold_id=3, draw_idx=7)
    assert key.filename() == "fold_03_draw_0007.pkl"


def test_filename_handles_large_indices() -> None:
    key = _lgb.LgbDrawKey(cfg_signature="abc" * 22, fold_id=99, draw_idx=9999)
    assert key.filename() == "fold_99_draw_9999.pkl"


def test_lgb_inner_cv_checkpoint_root_path(run_dir: Path) -> None:
    root = _lgb.lgb_inner_cv_checkpoint_root(run_dir)
    assert root == run_dir / "_lgb_inner_cv_checkpoints"


def test_lgb_inner_cv_cfg_dir_uses_truncated_signature(
    run_dir: Path,
) -> None:
    sig = "0123456789abcdef" + "X" * 48
    cfg_dir = _lgb.lgb_inner_cv_cfg_dir(run_dir, sig)
    assert cfg_dir.name == "0123456789abcdef"
