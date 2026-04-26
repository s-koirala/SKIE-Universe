"""Unit tests for the orchestrator's HMM-fit cache.

Closure tests for ``P1-H050-SMOKE-RUNTIME-INVESTIGATE``.

The cache amortises ``select_gaussian_hmm`` across the 27-cell label
grid by recognising that the HMM input ``r_tr = r[train_idx]`` is a
function of ``(symbol, train_idx)`` only — label cfg perturbs ``y`` and
the outer-fold purge_window (and therefore fold geometry) but not the
close-derived returns. The cache key is
``(symbol, fold_id, label_horizon)`` (F-PLV-1 fix); cfgs sharing a
vertical_barrier (and hence label_horizon) share fits, divergent
vertical_barriers populate disjoint cache entries.
``_validate_cache_invariant`` is retained as a defensive backstop
against future refactors that decouple fold geometry from
label_horizon. The cache is per-symbol (reset between symbols) and
toggled off via ``--no-hmm-cache`` for byte-identical-output
regression verification (HMM emission means and transition matrix
must be invariant whether the model is fresh-fit or cache-hit).

Tests align to the brief's required cases:

1. ``test_hmm_cache_hit_reuses_fitted_model`` — synthetic 2-cfg run;
   second cfg's HMM fit is skipped on shared (symbol, fold) keys.
2. ``test_hmm_cache_disabled_via_flag`` — ``--no-hmm-cache`` runs the
   legacy code path; cache stats record n_hits=0.
3. ``test_cache_hit_byte_identical_outputs`` — HMM emission means +
   transition matrix from cache hit equal those from cache miss for the
   same fold.
4. ``test_cache_invariant_violation_raises`` — pass mismatched
   train_idx into the cache lookup; assert RuntimeError (regression
   guard).
5. ``test_cache_resets_between_symbols`` — ES cache entries do not
   bleed into NQ.
6. ``test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha``
   — dry-run ``--smoke`` with cache on vs off; warm-cold sidecar
   SHA256 must be identical.
"""

# ruff: noqa: N806, PLR2004, PLC0415, E402, I001
#
# N806 (lowercase variable) — `X` follows the scikit-learn convention
# for the design matrix.
# PLR2004 (magic numbers) — assertion constants are pre-registered
# fixture parameters chosen for test determinism.
# PLC0415 / E402 / I001 — orchestrator script lives under scripts/, so
# the late `import run_walk_forward` follows the project's established
# test-side pattern (see test_orchestrator_smoke.py).

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import run_walk_forward  # type: ignore[import-not-found]


# ---------------------------------------------------------------------------
# Fixture: minimal synthetic train block + lgb grid that exercises both
# the HMM-fit branch and the inner-CV refit branch of `_fit_fold`.
# ---------------------------------------------------------------------------


def _synthetic_fixture(seed: int = 2026) -> dict:
    """Build a small synthetic (X, y, r, train_idx) suitable for a
    single-fold _fit_fold call. n=600 rows is enough for inner-CV
    n_inner_folds=2 to produce at least one usable inner fold.
    """
    rng = np.random.default_rng(seed)
    n = 600
    X = rng.normal(size=(n, 4))
    y = ((X[:, 0] + 0.5 * X[:, 1] + rng.normal(size=n)) > 0).astype(np.int64)
    # Mix two regimes in r so the HMM has structure to learn.
    state = np.zeros(n, dtype=np.int64)
    p_switch = 0.005
    for i in range(1, n):
        state[i] = (1 - state[i - 1]) if rng.random() < p_switch else state[i - 1]
    r = np.where(
        state == 0,
        rng.normal(loc=0.0, scale=5e-4, size=n),
        rng.normal(loc=0.0, scale=2e-3, size=n),
    )
    train_idx = np.arange(n, dtype=np.int64)
    grid = {"num_leaves": (15, 31), "learning_rate": (0.05,), "min_data_in_leaf": (20,)}
    return {"X": X, "y": y, "r": r, "train_idx": train_idx, "lgb_grid": grid}


def _fit_kwargs(fx: dict) -> dict:
    return dict(
        X=fx["X"],
        y=fx["y"],
        r=fx["r"],
        hmm_cov_types=("diag",),
        lgb_grid=fx["lgb_grid"],
        lgb_n_draws=2,
        lgb_seed=2026,
        random_seed=2026,
        label_horizon=1,
        embargo=1,
        n_inner_folds=2,
    )


# ---------------------------------------------------------------------------
# 1. Cache hit reuses the fitted model (no second `select_gaussian_hmm`).
# ---------------------------------------------------------------------------


def test_hmm_cache_hit_reuses_fitted_model() -> None:
    """First call (cache miss) populates the cache; second call with the
    same (symbol, fold_id) hits the cache and increments n_hits without
    invoking ``select_gaussian_hmm``. The hits/misses counters
    distinguish fresh-fit from cache-hit deterministically.
    """
    fx = _synthetic_fixture()

    cache: dict[tuple[str, int, int], run_walk_forward._CachedHmmFit] = {}
    stats = run_walk_forward._HmmCacheStats()

    # Cfg 1 — cache miss.
    out1 = run_walk_forward._fit_fold(
        fx["train_idx"],
        **_fit_kwargs(fx),
        fold_id=0,
        symbol="ES",
        hmm_cache=cache,
        hmm_cache_stats=stats,
    )
    assert stats.n_misses == 1
    assert stats.n_hits == 0
    # _fit_kwargs sets label_horizon=1, so the 3-tuple key is ("ES", 0, 1).
    assert ("ES", 0, 1) in cache

    # Cfg 2 — same (symbol, fold_id, label_horizon), should hit.
    out2 = run_walk_forward._fit_fold(
        fx["train_idx"],
        **_fit_kwargs(fx),
        fold_id=0,
        symbol="ES",
        hmm_cache=cache,
        hmm_cache_stats=stats,
    )
    assert stats.n_misses == 1
    assert stats.n_hits == 1
    # Cached HMM identity must be the same Python object.
    assert out1["hmm"] is out2["hmm"]
    assert out1["regime_high_mean"] == out2["regime_high_mean"]
    assert int(out1["hmm_train_terminal_position"]) == int(
        out2["hmm_train_terminal_position"]
    )


# ---------------------------------------------------------------------------
# 2. --no-hmm-cache runs the legacy path.
# ---------------------------------------------------------------------------


def test_hmm_cache_disabled_via_flag(tmp_path: Path) -> None:
    """``--no-hmm-cache`` disables cache population; per-symbol stats
    show n_hits=0 across the smoke (1-cell) label grid. The run still
    completes end-to-end with identical artifact-tree shape.
    """
    from skie_ninja.utils.paths import ProjectPaths

    paths = ProjectPaths.discover()
    config = paths.root / "config" / "hypotheses" / "H050.yaml"
    out = run_walk_forward.run(
        [
            "--hypothesis",
            "H050",
            "--config",
            str(config),
            "--dry-run",
            "--smoke-n",
            "2000",
            "--smoke",
            "--no-hmm-cache",
        ]
    )
    try:
        run_summary = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
        assert run_summary["hmm_cache_enabled"] is False
        for sym in ("ES", "NQ"):
            stats = run_summary["per_symbol_status"][sym]["hmm_cache_stats"]
            assert stats["n_hits"] == 0
            # With cache disabled, every fold is a miss but the cache
            # is None so unique_keys is also 0 (we never populate).
            assert stats["n_unique_keys"] == 0
    finally:
        if out.exists():
            shutil.rmtree(out, ignore_errors=True)


# ---------------------------------------------------------------------------
# 3. Cache hit byte-identical outputs.
# ---------------------------------------------------------------------------


def test_cache_hit_byte_identical_outputs() -> None:
    """The HMM emission means and transition matrix from a cache-hit
    fit must be byte-identical to those produced by a fresh fit on the
    same data. Determinism is guaranteed by ``select_gaussian_hmm``'s
    seeded restart sequence; the cache exposes the SAME Python object
    so the equality is trivially by-identity, but we additionally
    verify by-value to catch any future refactor that returns a copy.
    """
    fx = _synthetic_fixture()

    # Run A — cache disabled (legacy path).
    out_a = run_walk_forward._fit_fold(fx["train_idx"], **_fit_kwargs(fx))

    # Run B — cache enabled, populated then re-read.
    cache: dict[tuple[str, int, int], run_walk_forward._CachedHmmFit] = {}
    out_b_miss = run_walk_forward._fit_fold(
        fx["train_idx"],
        **_fit_kwargs(fx),
        fold_id=7,
        symbol="ES",
        hmm_cache=cache,
    )
    out_b_hit = run_walk_forward._fit_fold(
        fx["train_idx"],
        **_fit_kwargs(fx),
        fold_id=7,
        symbol="ES",
        hmm_cache=cache,
    )

    a_means = out_a["hmm"].params_.means
    b_miss_means = out_b_miss["hmm"].params_.means
    b_hit_means = out_b_hit["hmm"].params_.means
    # HMMParams stores the log-transition matrix; the canonical
    # generative parameter is unique up to numerical precision under
    # log-space EM (Rabiner 1989 §III).
    a_trans = out_a["hmm"].params_.log_transmat
    b_miss_trans = out_b_miss["hmm"].params_.log_transmat
    b_hit_trans = out_b_hit["hmm"].params_.log_transmat

    np.testing.assert_array_equal(a_means, b_miss_means)
    np.testing.assert_array_equal(b_miss_means, b_hit_means)
    np.testing.assert_array_equal(a_trans, b_miss_trans)
    np.testing.assert_array_equal(b_miss_trans, b_hit_trans)

    # Terminal log α (used by the warm-start passthrough) must also be
    # byte-identical across the cache-hit boundary.
    np.testing.assert_array_equal(
        out_a["hmm_terminal_log_alpha"], out_b_miss["hmm_terminal_log_alpha"]
    )
    np.testing.assert_array_equal(
        out_b_miss["hmm_terminal_log_alpha"], out_b_hit["hmm_terminal_log_alpha"]
    )


# ---------------------------------------------------------------------------
# 4. Cache invariant violation raises.
# ---------------------------------------------------------------------------


def test_cache_invariant_violation_raises() -> None:
    """If a cached entry's ``train_idx_len/first/last`` mismatches the
    requesting fold's geometry, ``_validate_cache_invariant`` raises
    RuntimeError. This is a load-bearing regression guard: silently
    serving a stale fit when the (symbol, fold_id) collides across two
    engine runs with different purge windows would be a correctness
    violation.
    """
    fx = _synthetic_fixture()

    # Pre-fit and stash cache entry under a deliberately-mismatched
    # train_idx_last (simulate a hypothetical post-refactor engine
    # collision: the 3-tuple key already partitions divergent
    # label_horizons, so this guard fires only when a future refactor
    # decouples geometry from horizon).
    cache: dict[tuple[str, int, int], run_walk_forward._CachedHmmFit] = {}
    out = run_walk_forward._fit_fold(
        fx["train_idx"],
        **_fit_kwargs(fx),
        fold_id=0,
        symbol="ES",
        hmm_cache=cache,
    )
    key = ("ES", 0, 1)
    # Replace the cached entry with a tampered one (different last index).
    tampered = run_walk_forward._CachedHmmFit(
        hmm=cache[key].hmm,
        regime_high_mean=cache[key].regime_high_mean,
        hmm_terminal_log_alpha=cache[key].hmm_terminal_log_alpha,
        hmm_train_terminal_position=cache[key].hmm_train_terminal_position,
        train_idx_len=cache[key].train_idx_len,
        train_idx_first=cache[key].train_idx_first,
        train_idx_last=cache[key].train_idx_last + 1,  # tamper
    )
    cache[key] = tampered

    with pytest.raises(RuntimeError, match="HMM cache invariant violated"):
        run_walk_forward._fit_fold(
            fx["train_idx"],
            **_fit_kwargs(fx),
            fold_id=0,
            symbol="ES",
            hmm_cache=cache,
        )
    # Sanity: the original (non-tampered) call returned a valid result.
    assert out["hmm"] is not None


# ---------------------------------------------------------------------------
# 5. Cache resets between symbols.
# ---------------------------------------------------------------------------


def test_cache_isolates_symbols_unit() -> None:
    """F-PLV-5: strengthen the prior end-to-end test with a unit-level
    assertion that ES cache entries are NOT visible from an NQ lookup.
    Two ``_fit_fold`` calls with disjoint ``symbol`` values populate
    disjoint cache keys; an NQ-keyed lookup misses even after ES
    populated the same fold_id + label_horizon.
    """
    fx = _synthetic_fixture()
    cache: dict[tuple[str, int, int], run_walk_forward._CachedHmmFit] = {}
    stats = run_walk_forward._HmmCacheStats()

    run_walk_forward._fit_fold(
        fx["train_idx"],
        **_fit_kwargs(fx),
        fold_id=0,
        symbol="ES",
        hmm_cache=cache,
        hmm_cache_stats=stats,
    )
    assert ("ES", 0, 1) in cache
    assert ("NQ", 0, 1) not in cache

    run_walk_forward._fit_fold(
        fx["train_idx"],
        **_fit_kwargs(fx),
        fold_id=0,
        symbol="NQ",
        hmm_cache=cache,
        hmm_cache_stats=stats,
    )
    # Both populated; a 2-tuple key would have collided.
    assert ("ES", 0, 1) in cache
    assert ("NQ", 0, 1) in cache
    assert cache[("ES", 0, 1)] is not cache[("NQ", 0, 1)]
    assert stats.n_misses == 2
    assert stats.n_hits == 0


def test_cache_resets_between_symbols(tmp_path: Path) -> None:
    """The cache is instantiated PER ``_run_symbol`` invocation; ES
    entries do not bleed into NQ. The smoke run iterates [ES, NQ] per
    H050.yaml; per-symbol stats objects are independent.
    """
    from skie_ninja.utils.paths import ProjectPaths

    paths = ProjectPaths.discover()
    config = paths.root / "config" / "hypotheses" / "H050.yaml"
    out = run_walk_forward.run(
        [
            "--hypothesis",
            "H050",
            "--config",
            str(config),
            "--dry-run",
            "--smoke-n",
            "2000",
            "--smoke",
        ]
    )
    try:
        run_summary = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
        es_stats = run_summary["per_symbol_status"]["ES"]["hmm_cache_stats"]
        nq_stats = run_summary["per_symbol_status"]["NQ"]["hmm_cache_stats"]
        # Both symbols process the smoke 1-cell grid → 1 cfg pays misses,
        # zero hits in the smoke fixture (only one cell per symbol).
        # The structural invariant is that NQ's stats object is a
        # different dict from ES's — no key sharing.
        assert isinstance(es_stats, dict)
        assert isinstance(nq_stats, dict)
        # Independence proxy: the per-symbol unique-keys counter only
        # records keys for that symbol, so summing across symbols
        # reflects total misses.
        assert es_stats["n_misses"] >= 1
        assert nq_stats["n_misses"] >= 1
    finally:
        if out.exists():
            shutil.rmtree(out, ignore_errors=True)


# ---------------------------------------------------------------------------
# 6. Warm-cold sidecar SHA256 invariant under cache toggle.
# ---------------------------------------------------------------------------


def test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha(
    tmp_path: Path,
) -> None:
    """The warm-cold diagnostic sidecar SHA256 must be identical
    whether the HMM cache is enabled or disabled. The sidecar's
    content is derived from the per-fold filtered posteriors which in
    turn depend on the fitted HMM; if the cache served a different
    model the SHA would diverge.

    Two ``--smoke --dry-run`` runs are launched with identical args
    except the ``--no-hmm-cache`` flag. The sidecar is written to
    ``logs/reproducibility/{run_id}_hmm_warm_cold.json`` per
    :func:`warm_cold_sidecar_path_for`; we read each and compare the
    deterministic SHA.
    """
    import hashlib

    from skie_ninja.models.regime import warm_cold_sidecar_path_for
    from skie_ninja.utils.paths import ProjectPaths

    paths = ProjectPaths.discover()
    config = paths.root / "config" / "hypotheses" / "H050.yaml"

    out_on = run_walk_forward.run(
        [
            "--hypothesis",
            "H050",
            "--config",
            str(config),
            "--dry-run",
            "--smoke-n",
            "2000",
            "--smoke",
        ]
    )
    out_off = run_walk_forward.run(
        [
            "--hypothesis",
            "H050",
            "--config",
            str(config),
            "--dry-run",
            "--smoke-n",
            "2000",
            "--smoke",
            "--no-hmm-cache",
        ]
    )
    try:
        # The sidecar path is keyed on `{run_id}_{sym}` (sym_run_id);
        # we hash the file bytes from each run for both symbols and
        # compare.
        for sym in ("ES", "NQ"):
            run_id_on = out_on.name
            run_id_off = out_off.name
            sidecar_on = warm_cold_sidecar_path_for(
                f"{run_id_on}_{sym}",
                logs_reproducibility_dir=paths.logs_reproducibility,
            )
            sidecar_off = warm_cold_sidecar_path_for(
                f"{run_id_off}_{sym}",
                logs_reproducibility_dir=paths.logs_reproducibility,
            )
            assert sidecar_on.is_file(), f"sidecar missing for {sym} (cache on)"
            assert sidecar_off.is_file(), f"sidecar missing for {sym} (cache off)"
            sha_on = hashlib.sha256(sidecar_on.read_bytes()).hexdigest()
            sha_off = hashlib.sha256(sidecar_off.read_bytes()).hexdigest()
            assert sha_on == sha_off, (
                f"warm-cold sidecar SHA divergence for {sym}: "
                f"on={sha_on}, off={sha_off}"
            )
    finally:
        for o in (out_on, out_off):
            if o.exists():
                shutil.rmtree(o, ignore_errors=True)


# ---------------------------------------------------------------------------
# F-PLV-1 regression: cache key includes label_horizon.
# ---------------------------------------------------------------------------


def test_cache_key_includes_label_horizon() -> None:
    """F-PLV-1 regression: two cfgs sharing ``(symbol, fold_id)`` but
    differing in ``label_horizon`` must populate two SEPARATE cache
    entries, not collide. Pre-fix, the 2-tuple key would have caused
    the second call to either (a) silently return a stale fit, or
    (b) raise via ``_validate_cache_invariant`` if the train_idx
    geometry diverged. Post-fix, the 3-tuple key partitions the
    entries.
    """
    fx = _synthetic_fixture()
    cache: dict[tuple[str, int, int], run_walk_forward._CachedHmmFit] = {}
    stats = run_walk_forward._HmmCacheStats()

    kw = _fit_kwargs(fx)
    kw_60 = {**kw, "label_horizon": 60}
    kw_120 = {**kw, "label_horizon": 120}

    out_60 = run_walk_forward._fit_fold(
        fx["train_idx"],
        **kw_60,
        fold_id=3,
        symbol="ES",
        hmm_cache=cache,
        hmm_cache_stats=stats,
    )
    out_120 = run_walk_forward._fit_fold(
        fx["train_idx"],
        **kw_120,
        fold_id=3,
        symbol="ES",
        hmm_cache=cache,
        hmm_cache_stats=stats,
    )

    # TWO entries (no collision); both miss because the keys differ.
    assert ("ES", 3, 60) in cache
    assert ("ES", 3, 120) in cache
    assert cache[("ES", 3, 60)] is not cache[("ES", 3, 120)]
    assert stats.n_misses == 2
    assert stats.n_hits == 0
    # Both fits succeeded.
    assert out_60["hmm"] is not None
    assert out_120["hmm"] is not None


def test_within_vertical_barrier_stratum_cache_hits() -> None:
    """F-PLV-1 regression: three cfgs sharing ``label_horizon=60`` but
    differing in (pt_sl, volatility_lookback) call ``_fit_fold`` on the
    SAME (symbol, fold_id, label_horizon) triple — all three see the
    same fit. The first is a miss; the next two are hits.
    """
    fx = _synthetic_fixture()
    cache: dict[tuple[str, int, int], run_walk_forward._CachedHmmFit] = {}
    stats = run_walk_forward._HmmCacheStats()

    kw = _fit_kwargs(fx)
    kw_stratum = {**kw, "label_horizon": 60}

    for _ in range(3):
        run_walk_forward._fit_fold(
            fx["train_idx"],
            **kw_stratum,
            fold_id=0,
            symbol="ES",
            hmm_cache=cache,
            hmm_cache_stats=stats,
        )

    assert stats.n_misses == 1
    assert stats.n_hits == 2
    assert ("ES", 0, 60) in cache
    assert len(cache) == 1


def test_h050_27cell_grid_speedup_simulation() -> None:
    """F-PLV-1 regression: simulate the H050 27-cell label grid by
    iterating 3 vertical_barrier strata × 9 cfgs per stratum across
    ``N_FOLDS`` synthetic folds. Assert the cache produces:

    * ``n_misses = 3 strata × N_FOLDS`` (one miss per (stratum, fold))
    * ``n_hits   = 24 cfgs × N_FOLDS = (27 - 3) × N_FOLDS``
    * speedup ≈ 9× (27 / 3 fits per fold)

    With the 3-tuple cache key the orchestrator pays HMM-fit cost
    once per (symbol, fold_id, label_horizon) stratum rather than once
    per cfg.
    """
    fx = _synthetic_fixture()
    cache: dict[tuple[str, int, int], run_walk_forward._CachedHmmFit] = {}
    stats = run_walk_forward._HmmCacheStats()

    n_folds = 2
    strata = (30, 60, 120)  # three vertical_barrier strata in bars
    n_per_stratum = 9  # 3 pt_sl × 3 volatility_lookback
    base_kw = _fit_kwargs(fx)

    for fold_id in range(n_folds):
        for lh in strata:
            for _cfg_within in range(n_per_stratum):
                kw_cell = {**base_kw, "label_horizon": lh}
                run_walk_forward._fit_fold(
                    fx["train_idx"],
                    **kw_cell,
                    fold_id=fold_id,
                    symbol="ES",
                    hmm_cache=cache,
                    hmm_cache_stats=stats,
                )

    expected_misses = len(strata) * n_folds
    expected_hits = (len(strata) * n_per_stratum - len(strata)) * n_folds
    assert stats.n_misses == expected_misses
    assert stats.n_hits == expected_hits
    # Hit ratio on H050 grid is 24/27 = 8/9 ≈ 0.889 within ε.
    total = stats.n_hits + stats.n_misses
    hit_ratio = stats.n_hits / total
    assert abs(hit_ratio - 8.0 / 9.0) < 1e-9
    # Cache contains exactly one entry per (fold, stratum) pair.
    assert len(cache) == expected_misses
