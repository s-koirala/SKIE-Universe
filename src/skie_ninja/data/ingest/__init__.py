"""Ingest sub-package — registry + concrete adapters."""

from skie_ninja.data.ingest._registry import INGEST_REGISTRY, IngestJob, register

__all__ = ["INGEST_REGISTRY", "IngestJob", "register"]
