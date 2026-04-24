"""Feature-factory Protocol, registry, and contractual-test base class.

Source of truth for the feature interface defined in
[plan/implementation-plan_2026-04-15.md] §3 (lines 101-132). Every
module registered here is enumerable by the walk-forward runner and
must satisfy the six contractual guarantees below.

Contractual guarantees (plan §3.1-3.6)
--------------------------------------

  1. **PIT (point-in-time)**. For any timestamp ``now``:
     ``compute(panel, now) == compute(panel.filter(ts <= now), now)``.
     The feature value at ``now`` depends only on rows whose
     ``ts_event <= now``. The :class:`FeatureTestBase` pytest mixin
     exercises this on 100 randomly drawn ``now`` values.

  2. **Determinism**. Same inputs → identical bytes. Verified via
     :func:`skie_ninja.utils.hashing.frame_sha256` in the same
     :class:`FeatureTestBase` helper.

  3. **No silent NaN**. Any NaN-admitting column must be declared as
     nullable in ``output_schema``. Features that only produce NaN on
     a documented boundary (e.g., warm-up of a rolling window) must
     name the column ``nullable=True`` and explain the pattern in
     the module docstring.

  4. **Provenance**. The assembly layer writes a per-feature JSON to
     ``logs/reproducibility/features/{name}_{version}_{run_id}.json``
     at run time; see :mod:`skie_ninja.features.assembly`.

  5. **Latency budget**. Caller-declared per-module — not enforced
     here; see the assembly-level timer which logs per-feature wall
     time into the provenance record.

  6. **Schema stability**. Any change to output column names or
     dtypes bumps ``version`` (semver: ``MAJOR.MINOR``).

The registry (``FEATURE_REGISTRY``) is populated at import time via
:func:`register_feature`. Sub-packages (``microstructure/`` etc.)
import all modules in their ``__init__.py`` so that a single
``import skie_ninja.features`` triggers full registration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.utils.hashing import frame_sha256


# ---------------------------------------------------------------------------
# Dataset reference (input declaration)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DatasetRef:
    """Reference to an input dataset that a :class:`FeatureModule`
    consumes.

    Fields
    ------
    name
        Dataset identifier, e.g. ``"vendor_legacy_1min_roll_adjusted"``.
        Matches the ``_DATASET_NAME`` constant used by the ingest layer.
    columns
        Tuple of required columns. Missing columns at ``compute`` time
        raise a ``ValueError`` — declared here for static inspection.
    min_lookback
        Minimum ``ts_event`` span the module needs to render a single
        row. Typed as ``pd.Timedelta`` to match the Protocol's
        ``lookback`` attribute.
    """

    name: str
    columns: tuple[str, ...]
    min_lookback: pd.Timedelta


# ---------------------------------------------------------------------------
# Feature-module Protocol (plan §3)
# ---------------------------------------------------------------------------


@runtime_checkable
class FeatureModule(Protocol):
    """Protocol every registered feature must satisfy.

    Verbatim from [plan/implementation-plan_2026-04-15.md] §3. The
    ``runtime_checkable`` decoration allows the registry to
    ``isinstance(obj, FeatureModule)`` at registration time — a
    cheap guard against accidentally registering an unrelated object.
    """

    name: str
    version: str
    lookback: pd.Timedelta
    inputs: tuple[DatasetRef, ...]
    output_schema: pa.Schema

    def compute(
        self, panel: pl.LazyFrame, now: pd.Timestamp, ctx: Any
    ) -> pl.LazyFrame:
        """Return the feature's output LazyFrame at or before ``now``.

        The output is a LazyFrame whose ``ts_event`` column is
        monotone non-decreasing and all of whose rows satisfy
        ``ts_event <= now``. Column dtypes match ``output_schema``.
        """
        ...

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        """Optional hook for module-specific PIT validation.

        The generic PIT invariant is checked by
        :class:`FeatureTestBase`; this hook is for module-specific
        invariants that are not visible to the generic checker (e.g.
        a module that pulls from an auxiliary ``release_ts`` column
        beyond the base panel).
        """
        ...


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


FEATURE_REGISTRY: dict[str, FeatureModule] = {}
"""Module-global feature registry keyed by ``"{name}@{version}"``.

Populated by :func:`register_feature`. The walk-forward runner
enumerates this dict to materialise the feature matrix; any
registered module must pass :class:`FeatureTestBase`'s
contractual-guarantee tests.
"""


def register_feature(module: FeatureModule) -> FeatureModule:
    """Register ``module`` under the key ``"{name}@{version}"``.

    Raises :class:`ValueError` on a double-registration of the same
    ``name@version`` — we refuse silent shadowing because two code
    paths producing conflicting outputs under the same key would
    defeat schema-stability guarantee §3.6.
    """
    if not isinstance(module, FeatureModule):
        raise TypeError(
            f"register_feature expects a FeatureModule Protocol; "
            f"got {type(module).__name__}."
        )
    key = f"{module.name}@{module.version}"
    if key in FEATURE_REGISTRY:
        existing = FEATURE_REGISTRY[key]
        if existing is module:
            return module
        raise ValueError(
            f"Feature {key!r} is already registered with a different "
            "object. Bump the version per plan §3.6 schema stability."
        )
    FEATURE_REGISTRY[key] = module
    return module


def clear_registry_for_test() -> None:
    """Test-only helper — drop all entries. Not exported in ``__all__``
    of the package root.
    """
    FEATURE_REGISTRY.clear()


# ---------------------------------------------------------------------------
# FeatureTestBase — pytest mixin for contractual guarantees
# ---------------------------------------------------------------------------


class FeatureTestBase:
    """pytest mixin that exercises the contractual guarantees.

    Concrete subclasses override :meth:`make_module` and
    :meth:`make_panel`. The tests declared here then run against the
    produced module / panel pair. Subclasses may add their own
    ``test_*`` methods (e.g. analytical-case checks for a specific
    formula) in addition to the inherited ones.

    Why a test base, not a function library? pytest picks up the
    class when it appears in ``tests/unit/test_features_*.py``; the
    inheritance gives one concrete test file per feature and
    registers all contractual tests automatically — no need for
    parametrization boilerplate.
    """

    # Override in subclass.
    def make_module(self) -> FeatureModule:
        raise NotImplementedError

    def make_panel(self) -> pl.LazyFrame:
        raise NotImplementedError

    def sample_timestamps(self, n: int = 100) -> list[pd.Timestamp]:
        """Random ``now`` timestamps spanning the panel span.

        Uses a :class:`numpy.random.Generator` seeded at 2026 so the
        sample set is reproducible. The count ``n=100`` is the
        plan §3.1 contract target — increasing it trades runtime for
        statistical coverage, but 100 is sufficient to catch a PIT
        regression on any feature whose state is contiguous in time.
        """
        panel = self.make_panel().collect()
        ts = panel.get_column("ts_event").to_pandas()
        if len(ts) == 0:
            return []
        rng = np.random.default_rng(2026)
        indices = rng.integers(low=1, high=len(ts), size=n)
        return [ts.iloc[int(i)] for i in indices]

    # ------------------------------------------------------------------
    # PIT — guarantee §3.1
    # ------------------------------------------------------------------

    def test_pit_invariant(self) -> None:
        """At every ``now``, ``compute(full, now) == compute(panel≤now, now)``.

        Runs the plan §3.1 contract check on 100 random ``now``
        timestamps. Disagreement indicates the feature consumes rows
        with ``ts_event > now`` — a look-ahead leak.
        """
        module = self.make_module()
        panel = self.make_panel()
        full = panel.collect()
        ctx = _NullRunContext()
        # Local import to avoid a circular dependency — ``windowing``
        # imports nothing from ``base`` directly, but keeping the
        # import lazy makes the dependency direction obvious to a
        # reader.
        from skie_ninja.features.windowing import _pit_cutoff

        for now in self.sample_timestamps(n=100):
            truncated = full.filter(
                pl.col("ts_event") <= _pit_cutoff(now)
            ).lazy()
            out_full = module.compute(panel, now, ctx).collect()
            out_trunc = module.compute(truncated, now, ctx).collect()
            # Hash equality: row-permutation invariant via
            # frame_sha256; every column compared.
            sort_cols = ["ts_event"]
            if "symbol" in out_full.columns:
                sort_cols = ["symbol", "ts_event"]
            hf = frame_sha256(out_full, sort_cols=sort_cols)
            ht = frame_sha256(out_trunc, sort_cols=sort_cols)
            assert hf == ht, (
                f"PIT violation in {module.name}@{module.version} at "
                f"now={now!r}: compute(panel, now) != "
                "compute(panel.filter(ts<=now), now)."
            )

    # ------------------------------------------------------------------
    # Determinism — guarantee §3.2
    # ------------------------------------------------------------------

    def test_determinism(self) -> None:
        """Same inputs → same hash. Two back-to-back computes must
        produce byte-identical canonical frames.
        """
        module = self.make_module()
        panel = self.make_panel()
        ctx = _NullRunContext()
        now = self.sample_timestamps(n=1)
        if not now:
            return
        out1 = module.compute(panel, now[0], ctx).collect()
        out2 = module.compute(panel, now[0], ctx).collect()
        sort_cols = ["ts_event"]
        if "symbol" in out1.columns:
            sort_cols = ["symbol", "ts_event"]
        assert frame_sha256(out1, sort_cols=sort_cols) == frame_sha256(
            out2, sort_cols=sort_cols
        )

    # ------------------------------------------------------------------
    # No silent NaN — guarantee §3.3
    # ------------------------------------------------------------------

    def test_no_silent_nan(self) -> None:
        """Any NaN in the output must correspond to a column declared
        nullable in ``output_schema``.

        Silent NaN (column not declared nullable but contains NaN) is
        a §3.3 violation.
        """
        module = self.make_module()
        panel = self.make_panel()
        ctx = _NullRunContext()
        now = self.sample_timestamps(n=1)
        if not now:
            return
        out = module.compute(panel, now[0], ctx).collect()
        nullable_fields = {
            field.name: field.nullable for field in module.output_schema
        }
        for col in out.columns:
            if col not in nullable_fields:
                # Output column not in schema is a separate schema-
                # stability failure — let :meth:`test_output_schema`
                # catch it; don't double-report here.
                continue
            n_null = out.get_column(col).null_count()
            if n_null > 0 and not nullable_fields[col]:
                raise AssertionError(
                    f"{module.name}@{module.version}: column {col!r} "
                    f"has {n_null} null(s) but is declared non-nullable "
                    "in output_schema (guarantee §3.3)."
                )

    # ------------------------------------------------------------------
    # Schema stability — guarantee §3.6
    # ------------------------------------------------------------------

    def test_output_schema(self) -> None:
        """Output columns are a subset of ``output_schema`` fields.

        The module may legitimately return fewer rows than the schema
        documents (e.g., a module pruned empty columns to save
        memory); but it must not return a column that isn't declared.
        """
        module = self.make_module()
        panel = self.make_panel()
        ctx = _NullRunContext()
        now = self.sample_timestamps(n=1)
        if not now:
            return
        out = module.compute(panel, now[0], ctx).collect()
        declared = {field.name for field in module.output_schema}
        for col in out.columns:
            assert col in declared, (
                f"{module.name}@{module.version} emitted undeclared "
                f"column {col!r}. Declared columns: {sorted(declared)}."
            )


# ---------------------------------------------------------------------------
# Null RunContext — used by the test base so we don't need to open a
# real :class:`~skie_ninja.utils.runcontext.RunContext` (which writes a
# ReproLog at exit).
# ---------------------------------------------------------------------------


class _NullRunContext:
    """Stand-in for :class:`~skie_ninja.utils.runcontext.RunContext`
    that accepts arbitrary attribute access.

    Used by :class:`FeatureTestBase` so tests don't have to open a
    real RunContext (which would write a ReproLog to disk). Feature
    modules that call ``ctx.log.anything`` during compute should
    guard or keep their usage to ``getattr(ctx, 'name', default)``.
    """

    def __getattr__(self, _name: str) -> Any:
        return None


__all__ = [
    "DatasetRef",
    "FEATURE_REGISTRY",
    "FeatureModule",
    "FeatureTestBase",
    "clear_registry_for_test",
    "register_feature",
]
