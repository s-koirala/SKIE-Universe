"""Deterministic hashing helpers.

All hashes are SHA-256 hex digests. The chunk size for file reads
(1 MiB) is the common page-cache-friendly value used by `hashlib`
examples in CPython docs and has no statistical content; it is an
I/O throughput tuning parameter only.

Environment pinning: `frame_sha256` uses polars string casting, so
hash stability is tied to the polars primitive-formatting contract.
On any polars MAJOR-version upgrade, bump `ReproLog.env_id` so
downstream verifiers flag the boundary rather than silently
accepting mismatches.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any

_FILE_CHUNK_BYTES = 1 << 20  # 1 MiB; I/O-tuning only, no statistical meaning

# Canonical column separator for frame canonicalization. NUL cannot
# appear inside a polars Utf8 value, so using it as the inter-cell
# delimiter makes the canonicalization prefix-free without escaping.
_CELL_SEP = b"\x00"
_ROW_SEP = b"\x00\x01"


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(_FILE_CHUNK_BYTES), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_polars(df: Any) -> bool:
    return type(df).__module__.startswith("polars")


def _is_pandas(df: Any) -> bool:
    return type(df).__module__.startswith("pandas")


def _canonicalize_polars(df: Any, sort_cols: list[str]) -> bytes:
    """Column-wise stable canonicalization of a polars DataFrame.

    Steps:
      1. Sort rows by `sort_cols` (deterministic, not maintain_order).
      2. For each column, cast to Utf8. Binary columns are hex-encoded
         first to keep the representation printable and stable across
         polars versions.
      3. Join cells within a row with NUL, rows with NUL+SOH.

    This avoids polars IPC, whose binary layout has changed across
    minor versions (see polars-rs release notes) and is not a
    supported hash-stability surface.
    """
    import polars as pl

    if isinstance(df, pl.LazyFrame):
        df = df.collect()
    sorted_df = df.sort(sort_cols, maintain_order=False)

    # Column order: sort columns first in the provided order, then
    # remaining columns in lexicographic order. Guarantees stability
    # regardless of input column ordering.
    remaining = sorted(c for c in sorted_df.columns if c not in sort_cols)
    ordered_cols = list(sort_cols) + remaining
    sorted_df = sorted_df.select(ordered_cols)

    # Cast each column to Utf8 via an explicit branch for binary.
    cast_exprs = []
    for name in ordered_cols:
        dtype = sorted_df.schema[name]
        if dtype == pl.Binary:
            # hex-encode; polars does not have a built-in hex cast,
            # so use bin.encode when available (polars >= 1.0) and
            # fall back to a Python-side map.
            try:
                cast_exprs.append(pl.col(name).bin.encode("hex").alias(name))
            except AttributeError:
                cast_exprs.append(
                    pl.col(name)
                    .map_elements(
                        lambda b: b.hex() if b is not None else None,
                        return_dtype=pl.Utf8,
                    )
                    .alias(name)
                )
        else:
            cast_exprs.append(pl.col(name).cast(pl.Utf8).alias(name))
    str_df = sorted_df.with_columns(cast_exprs)

    rows = str_df.rows()
    out = io.BytesIO()
    for i, row in enumerate(rows):
        if i > 0:
            out.write(_ROW_SEP)
        for j, cell in enumerate(row):
            if j > 0:
                out.write(_CELL_SEP)
            # None is distinct from empty string to avoid hash collision.
            if cell is None:
                out.write(b"\x02NULL")
            else:
                out.write(str(cell).encode("utf-8"))
    # Prefix with a header of column names + dtype names so a schema
    # change yields a different hash even with identical values.
    header = "\x00".join(
        f"{c}:{sorted_df.schema[c]}" for c in ordered_cols
    ).encode("utf-8")
    return header + b"\x00\x03" + out.getvalue()


def frame_sha256(df: Any, sort_cols: list[str]) -> str:
    """Hash a dataframe after stable-sorting by `sort_cols`.

    Row permutations of the input yield the same hash; any value
    mutation changes the hash. Works for pandas or polars frames.
    Canonicalization is a column-wise Utf8 cast (see
    `_canonicalize_polars`), not IPC/Arrow bytes, so hashes are
    stable across polars MINOR versions.

    Bump `ReproLog.env_id` on polars MAJOR upgrades — the Utf8
    formatting of floats in particular is a polars-version surface.
    """
    if not sort_cols:
        raise ValueError("sort_cols must be non-empty for deterministic hashing")

    if _is_polars(df):
        canonical = _canonicalize_polars(df, sort_cols)
        return hashlib.sha256(canonical).hexdigest()

    if _is_pandas(df):
        import polars as pl

        # Route via polars so pandas and polars inputs with the same
        # logical content produce identical bytes.
        canonical = _canonicalize_polars(pl.from_pandas(df), sort_cols)
        return hashlib.sha256(canonical).hexdigest()

    raise TypeError(f"Unsupported dataframe type: {type(df)!r}")


def model_sha256(obj: Any) -> str:
    """Hash a model artifact.

    Supported (canonically hashable) inputs:

    - torch `state_dict` — a `dict` whose values are all
      `torch.Tensor`. Serialized by sorting keys alphabetically, then
      `torch.save` into an in-memory buffer. `torch.save` is
      deterministic for a fixed torch version and tensor dtype/layout,
      which is what `ReproLog.env_id` pins.
    - sklearn estimators or other canonically picklable objects —
      serialized via `joblib.dump` to bytes. `joblib` handles numpy
      arrays deterministically; bump `env_id` on `joblib` or
      `scikit-learn` major upgrades.
    - `dict` / `list` / `tuple` / primitive scalars — serialized via
      `joblib.dump`, which uses pickle protocol 5 with stable numpy
      handling. Dicts are sorted by key before serialization so
      iteration order (controlled by `PYTHONHASHSEED`) does not leak
      into the bytes.

    Explicitly rejected (non-deterministic iteration order):

    - `set`, `frozenset`, or any dict with non-sortable keys —
      `TypeError` raised.
    """
    import joblib

    if isinstance(obj, set | frozenset):
        raise TypeError(
            "model_sha256 refuses set/frozenset inputs: iteration order "
            "depends on PYTHONHASHSEED and would not be deterministic "
            "across processes. Canonicalize to a sorted list first."
        )

    if isinstance(obj, dict) and obj and _looks_like_state_dict(obj):
        import torch

        buf = io.BytesIO()
        ordered = {k: obj[k] for k in sorted(obj.keys())}
        torch.save(ordered, buf)
        return hashlib.sha256(buf.getvalue()).hexdigest()

    canonical = _canonicalize_for_joblib(obj)
    buf = io.BytesIO()
    joblib.dump(canonical, buf, protocol=5)
    return hashlib.sha256(buf.getvalue()).hexdigest()


def _canonicalize_for_joblib(obj: Any) -> Any:
    """Walk `obj` and replace dicts/sets with order-stable structures.

    - dict -> list of (key, canonicalized_value) pairs sorted by key.
      Requires keys to be sortable and mutually comparable; otherwise
      `TypeError`.
    - set/frozenset -> rejected (see `model_sha256`).
    - list/tuple -> recursed element-wise; original type preserved.
    - other -> returned as-is. Non-canonical custom classes are the
      caller's responsibility; this function does not try to guess.
    """
    if isinstance(obj, set | frozenset):
        raise TypeError(
            "Nested set/frozenset is not canonically hashable; "
            "convert to sorted list before calling model_sha256."
        )
    if isinstance(obj, dict):
        try:
            keys = sorted(obj.keys())
        except TypeError as exc:
            raise TypeError(
                "model_sha256 requires dict keys to be sortable; "
                f"got keys of heterogeneous types: {list(obj.keys())!r}"
            ) from exc
        return [(k, _canonicalize_for_joblib(obj[k])) for k in keys]
    if isinstance(obj, list):
        return [_canonicalize_for_joblib(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_canonicalize_for_joblib(x) for x in obj)
    return obj


def _looks_like_state_dict(obj: dict[Any, Any]) -> bool:
    try:
        import torch
    except ImportError:
        return False
    return all(isinstance(v, torch.Tensor) for v in obj.values())
