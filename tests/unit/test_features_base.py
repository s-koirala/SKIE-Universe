"""Registry contract tests for the feature base."""

from __future__ import annotations

from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from skie_ninja.features.base import (
    FEATURE_REGISTRY,
    DatasetRef,
    FeatureModule,
    register_feature,
)


class _DummyFeature:
    name = "__dummy__"
    version = "0.1"
    lookback = pd.Timedelta(minutes=1)
    inputs: tuple[DatasetRef, ...] = ()
    output_schema = pa.schema(
        [pa.field("ts_event", pa.timestamp("ns", tz="UTC"), nullable=False)]
    )

    def compute(
        self, panel: pl.LazyFrame, now: pd.Timestamp, ctx: Any
    ) -> pl.LazyFrame:
        return panel

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        _ = sample_ts


def test_registry_contains_four_microstructure_features() -> None:
    # Importing the features package registers the four microstructure
    # modules; they should be present by name+version.
    import skie_ninja.features  # noqa: F401

    expected = {
        "rv_parkinson@1.0",
        "rv_realized@1.0",
        "realized_skew@1.0",
        "ofi_tickrule@1.0",
    }
    assert expected.issubset(FEATURE_REGISTRY.keys())


def test_register_feature_refuses_double_registration_with_different_obj() -> None:
    a = _DummyFeature()
    b = _DummyFeature()
    # Both claim the same name@version but are distinct objects.
    register_feature(a)
    try:
        with pytest.raises(ValueError, match="already registered"):
            register_feature(b)
    finally:
        # Clean up so the test is idempotent.
        FEATURE_REGISTRY.pop("__dummy__@0.1", None)


def test_register_feature_idempotent_same_object() -> None:
    a = _DummyFeature()
    try:
        register_feature(a)
        # Re-registering the same instance is a no-op.
        register_feature(a)
        assert FEATURE_REGISTRY["__dummy__@0.1"] is a
    finally:
        FEATURE_REGISTRY.pop("__dummy__@0.1", None)


def test_register_feature_rejects_non_protocol_objects() -> None:
    class NotAModule:
        pass

    with pytest.raises(TypeError, match="FeatureModule"):
        register_feature(NotAModule())  # type: ignore[arg-type]


def test_feature_protocol_runtime_checkable() -> None:
    assert isinstance(_DummyFeature(), FeatureModule)
