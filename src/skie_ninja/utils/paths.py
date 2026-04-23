"""Project path resolver.

Single source of truth for filesystem layout. No module under
`skie_ninja` may hard-code absolute paths or construct paths relative
to `__file__` outside of this module (enforced by a grep-guard test
per plan P0-2).

Root discovery: walk up from this file until a directory containing
`pyproject.toml` is found. This keeps the resolver portable across
developer machines, CI runners, and Windows/POSIX hosts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _discover_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError(
        f"Could not locate project root (pyproject.toml) walking up from {start}"
    )


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved project directories.

    Construct via `ProjectPaths.discover()` or inject `root` directly
    for tests. All properties return `pathlib.Path`. Nothing is
    auto-created; callers that need the directory to exist call
    `.ensure()` explicitly.
    """

    root: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> ProjectPaths:
        origin = (start or Path(__file__)).resolve()
        return cls(root=_discover_root(origin))

    # Data
    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def data_raw(self) -> Path:
        return self.data / "raw"

    @property
    def data_interim(self) -> Path:
        return self.data / "interim"

    @property
    def data_processed(self) -> Path:
        return self.data / "processed"

    # Artifacts
    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def artifacts_models(self) -> Path:
        return self.artifacts / "models"

    @property
    def artifacts_reports(self) -> Path:
        return self.artifacts / "reports"

    @property
    def artifacts_runs(self) -> Path:
        return self.artifacts / "runs"

    @property
    def universe_log(self) -> Path:
        return self.artifacts / "universe" / "universe_log.parquet"

    # Logs
    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def logs_reproducibility(self) -> Path:
        return self.logs / "reproducibility"

    @property
    def logs_reproducibility_env(self) -> Path:
        return self.logs_reproducibility / "env"

    @property
    def logs_reproducibility_features(self) -> Path:
        return self.logs_reproducibility / "features"

    # Shared cross-project data directory
    # Resolution order: SKIE_SHARED_DATA env var > ~/datasets fallback.
    @property
    def shared_data(self) -> Path:
        """Shared machine-wide data root for vendor/raw datasets.

        Resolves ``SKIE_SHARED_DATA`` env var first (for CI or
        non-default locations), then falls back to ``~/datasets``.
        """
        env = os.environ.get("SKIE_SHARED_DATA")
        if env:
            return Path(env).expanduser().resolve()
        return Path.home() / "datasets"

    @property
    def shared_fred(self) -> Path:
        return self.shared_data / "fred"

    @property
    def shared_fomc_text(self) -> Path:
        return self.shared_data / "fomc_text"

    @property
    def shared_spf(self) -> Path:
        return self.shared_data / "spf"

    @property
    def shared_es_tick(self) -> Path:
        return self.shared_data / "es_tick"

    @property
    def shared_nq_tick(self) -> Path:
        return self.shared_data / "nq_tick"

    @property
    def shared_vendor_skie_ninja_legacy(self) -> Path:
        """Vendor-namespaced cache for parquet/CSV imports from the
        sibling SKIE_Ninja research repo (Databento-sourced ES 5-min
        features, 2020–2025). Kept as its own namespace so provenance +
        license + retrieval_date remain attached to the bytes and this
        repo does not couple to the sibling's filesystem layout.
        """
        return self.shared_data / "vendor_skie_ninja_legacy"

    def ensure(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path
