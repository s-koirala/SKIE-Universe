"""Unit tests for ``vendor_legacy_1min`` YAML-injectable sources.

Covers ``load_sources_yaml`` schema enforcement, ``merge_sources``
filename-collision precedence, and the constructor's ``sources``
override path used by the ``--sources-yaml`` CLI flag.

No network, no sibling-repo dependency — all fixtures synthesized
under ``tmp_path``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from skie_ninja.data.ingest.vendor_legacy_1min import (
    _CANONICAL_SOURCES,
    VendorLegacy1minIngestJob,
    _SourceFile,
    load_sources_yaml,
    merge_sources,
)

# ---------------------------------------------------------------------------
# load_sources_yaml — schema enforcement
# ---------------------------------------------------------------------------


class TestLoadSourcesYaml:
    def _write(self, path: Path, content: str) -> Path:
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_cell_i_eleven_entry_manifest(self, tmp_path: Path) -> None:
        """Cell I backfill case: 5 ES + 5 NQ + 1 NQ-2025 = 11 entries."""
        yaml_text = """
sources:
  - {symbol: ES, coverage: backfill_2015, filename: ES_2015_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2016, filename: ES_2016_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2017, filename: ES_2017_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2018, filename: ES_2018_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2019, filename: ES_2019_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2015, filename: NQ_2015_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2016, filename: NQ_2016_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2017, filename: NQ_2017_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2018, filename: NQ_2018_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2019, filename: NQ_2019_1min_databento.csv}
  - {symbol: NQ, coverage: forward_2025, filename: NQ_2025_1min_databento.csv}
"""
        p = self._write(tmp_path / "cell_i.yaml", yaml_text)
        out = load_sources_yaml(p)
        cell_i_count = 11
        assert len(out) == cell_i_count
        assert all(isinstance(s, _SourceFile) for s in out)
        # Filenames match the Cell-I pattern documented in the runbook.
        filenames = {s.filename for s in out}
        assert "ES_2015_1min_databento.csv" in filenames
        assert "NQ_2025_1min_databento.csv" in filenames
        # Symbol restricted to ES, NQ for Cell I.
        assert {s.symbol for s in out} == {"ES", "NQ"}

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Sources YAML not found"):
            load_sources_yaml(tmp_path / "absent.yaml")

    def test_missing_top_level_sources_key(self, tmp_path: Path) -> None:
        p = self._write(tmp_path / "bad.yaml", "other_key: []\n")
        with pytest.raises(ValueError, match="top-level key 'sources'"):
            load_sources_yaml(p)

    def test_sources_must_be_list(self, tmp_path: Path) -> None:
        p = self._write(tmp_path / "bad.yaml", "sources: not_a_list\n")
        with pytest.raises(ValueError, match="must be a list"):
            load_sources_yaml(p)

    def test_entry_must_be_mapping(self, tmp_path: Path) -> None:
        p = self._write(tmp_path / "bad.yaml", "sources:\n  - bare_string\n")
        with pytest.raises(ValueError, match="must be a mapping"):
            load_sources_yaml(p)

    def test_entry_missing_required_key(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path / "bad.yaml",
            "sources:\n  - {symbol: ES, coverage: backfill_2015}\n",
        )
        with pytest.raises(ValueError, match="missing keys"):
            load_sources_yaml(p)

    def test_entry_unknown_symbol(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path / "bad.yaml",
            "sources:\n  - {symbol: CL, coverage: c, filename: x.csv}\n",
        )
        with pytest.raises(ValueError, match="not in"):
            load_sources_yaml(p)

    def test_entry_filename_must_be_csv(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path / "bad.yaml",
            "sources:\n  - {symbol: ES, coverage: c, filename: x.parquet}\n",
        )
        with pytest.raises(ValueError, match="non-empty .csv name"):
            load_sources_yaml(p)

    def test_entry_filename_empty(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path / "bad.yaml",
            "sources:\n  - {symbol: ES, coverage: c, filename: ''}\n",
        )
        with pytest.raises(ValueError, match="non-empty .csv name"):
            load_sources_yaml(p)

    def test_entry_duplicate_filename_within_yaml(self, tmp_path: Path) -> None:
        yaml_text = """
sources:
  - {symbol: ES, coverage: a, filename: dup.csv}
  - {symbol: NQ, coverage: b, filename: dup.csv}
"""
        p = self._write(tmp_path / "bad.yaml", yaml_text)
        with pytest.raises(ValueError, match="duplicate filename"):
            load_sources_yaml(p)


# ---------------------------------------------------------------------------
# merge_sources — canonical takes precedence on filename collision
# ---------------------------------------------------------------------------


class TestMergeSources:
    def test_appends_new_entries(self) -> None:
        extra = (
            _SourceFile("ES", "backfill_2015", "ES_2015_1min_databento.csv"),
            _SourceFile("NQ", "backfill_2015", "NQ_2015_1min_databento.csv"),
        )
        merged = merge_sources(_CANONICAL_SOURCES, extra)
        assert len(merged) == len(_CANONICAL_SOURCES) + len(extra)
        # Canonical entries preserved at the head.
        assert merged[: len(_CANONICAL_SOURCES)] == _CANONICAL_SOURCES
        # Extras appended at the tail.
        assert merged[-2:] == extra

    def test_canonical_collision_drops_extra(self, caplog) -> None:
        """Filename matching a canonical entry must be dropped, not duplicated."""
        # ES_2020_1min_databento.csv is already in _CANONICAL_SOURCES.
        extra = (
            _SourceFile("ES", "OVERRIDE_2020", "ES_2020_1min_databento.csv"),
            _SourceFile("ES", "backfill_2015", "ES_2015_1min_databento.csv"),
        )
        with caplog.at_level("INFO"):
            merged = merge_sources(_CANONICAL_SOURCES, extra)
        # Length = canonical + 1 (only the new 2015 entry, not the 2020 override).
        assert len(merged) == len(_CANONICAL_SOURCES) + 1
        assert merged[-1].filename == "ES_2015_1min_databento.csv"
        # Original canonical 2020 entry preserved untouched.
        canonical_2020 = next(
            s for s in merged if s.filename == "ES_2020_1min_databento.csv"
        )
        assert canonical_2020.coverage == "oos_2020"
        # Shadow event was logged.
        assert any("shadowed by canonical" in r.message for r in caplog.records)

    def test_extra_internal_dedup_preserves_first_seen(self) -> None:
        """If extra has same-filename twice (caller error), merge_sources keeps first."""
        # Note: load_sources_yaml already raises on this case; merge_sources
        # is defensive in case a caller bypasses load_sources_yaml.
        extra = (
            _SourceFile("ES", "first", "ES_NEW.csv"),
            _SourceFile("ES", "second", "ES_NEW.csv"),
        )
        merged = merge_sources(_CANONICAL_SOURCES, extra)
        assert len(merged) == len(_CANONICAL_SOURCES) + 1
        assert merged[-1].coverage == "first"


# ---------------------------------------------------------------------------
# Constructor wiring — sources kwarg overrides _CANONICAL_SOURCES
# ---------------------------------------------------------------------------


class TestConstructorSourcesOverride:
    def test_default_sources_is_canonical_tuple(self) -> None:
        job = VendorLegacy1minIngestJob()
        assert job._sources == _CANONICAL_SOURCES

    def test_sources_kwarg_overrides(self) -> None:
        custom = (
            _SourceFile("ES", "backfill_2015", "ES_2015_1min_databento.csv"),
        )
        job = VendorLegacy1minIngestJob(sources=custom)
        assert job._sources == custom

    def test_merged_sources_preserves_filename_pattern(
        self, tmp_path: Path
    ) -> None:
        """Regression gate: tuple length and filename pattern after merge.

        The Cell I runbook depends on this exact behaviour: the YAML
        layer extends the canonical list, all filenames match the
        Databento naming convention, and the constructor accepts the
        merged tuple.
        """
        yaml_text = """
sources:
  - {symbol: ES, coverage: backfill_2015, filename: ES_2015_1min_databento.csv}
  - {symbol: NQ, coverage: forward_2025, filename: NQ_2025_1min_databento.csv}
"""
        p = tmp_path / "manifest.yaml"
        p.write_text(yaml_text, encoding="utf-8")

        extra = load_sources_yaml(p)
        merged = merge_sources(_CANONICAL_SOURCES, extra)

        # Tuple length matches expected.
        assert len(merged) == len(_CANONICAL_SOURCES) + 2

        # Every filename matches the documented Databento pattern.
        # Either {SYMBOL}_{YEAR}_1min_databento.csv or
        # {SYMBOL}_1min_databento.csv (combined-window).
        pattern = re.compile(
            r"^(ES|NQ|MES|MNQ)(_\d{4})?_1min_databento\.csv$"
        )
        for s in merged:
            assert pattern.match(s.filename), f"Bad filename: {s.filename}"

        # Constructor accepts the merged tuple without raising.
        job = VendorLegacy1minIngestJob(sources=merged)
        assert job._sources == merged
