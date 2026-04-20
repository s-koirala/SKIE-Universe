"""Pre-commit hook: validate that reproducible notebooks carry a ReproLog cell.

Rule (plan §9.1, §9.3): any notebook under ``notebooks/reproducible/`` must
contain at least one code cell whose outputs include a ``text/plain`` payload
that parses as JSON into a dict holding ALL 13 ReproLog fields defined in
plan §9.3::

    run_id, phase, hypothesis_id, timestamp_utc, git_head,
    pip_freeze_sha256, pip_freeze_path, dataset_checksums,
    rng_seed, model_hash, config_resolved_sha256, host, env_id

Exits non-zero with a precise missing-keys message if no cell satisfies the
contract.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FIELDS: frozenset[str] = frozenset(
    {
        "run_id",
        "phase",
        "hypothesis_id",
        "timestamp_utc",
        "git_head",
        "pip_freeze_sha256",
        "pip_freeze_path",
        "dataset_checksums",
        "rng_seed",
        "model_hash",
        "config_resolved_sha256",
        "host",
        "env_id",
    }
)


def _iter_text_plain_payloads(cell: dict) -> list[str]:
    """Yield every text/plain payload string attached to a cell's outputs."""
    payloads: list[str] = []
    for output in cell.get("outputs", []):
        data = output.get("data", {}) or {}
        payload = data.get("text/plain")
        if isinstance(payload, list):
            payloads.append("".join(str(p) for p in payload))
        elif isinstance(payload, str):
            payloads.append(payload)
        # Stream outputs sometimes carry the dump too.
        text = output.get("text")
        if isinstance(text, list):
            payloads.append("".join(text))
        elif isinstance(text, str):
            payloads.append(text)
    return payloads


def _try_parse_json_dict(blob: str) -> dict | None:
    """Attempt to parse *blob* as a JSON object.

    Jupyter often wraps repr output in single quotes; strip one pair of
    surrounding quotes before parsing as a best-effort fallback.
    """
    blob = blob.strip()
    if not blob:
        return None
    candidates = [blob]
    if (blob.startswith("'") and blob.endswith("'")) or (
        blob.startswith('"') and blob.endswith('"')
    ):
        candidates.append(blob[1:-1])
    for cand in candidates:
        try:
            obj = json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict):
            return obj
    return None


def check_notebook(path: Path) -> list[str]:
    """Return a list of error strings; empty means pass."""
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: cannot parse notebook ({exc})"]

    best_missing: set[str] | None = None
    saw_any_json_dict = False

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for blob in _iter_text_plain_payloads(cell):
            parsed = _try_parse_json_dict(blob)
            if parsed is None:
                continue
            saw_any_json_dict = True
            present = set(parsed.keys())
            missing = REQUIRED_FIELDS - present
            if not missing:
                return []
            if best_missing is None or len(missing) < len(best_missing):
                best_missing = missing

    if not saw_any_json_dict:
        return [
            f"{path}: no code-cell output contains a JSON-dict ReproLog dump. "
            f"Expected a text/plain payload parseable as a JSON object with "
            f"all {len(REQUIRED_FIELDS)} fields from plan §9.3."
        ]

    assert best_missing is not None
    return [
        f"{path}: ReproLog dump is missing required field(s): "
        f"{sorted(best_missing)}. "
        f"Expected all {len(REQUIRED_FIELDS)} fields from plan §9.3."
    ]


def main(argv: list[str]) -> int:
    errors: list[str] = []
    for arg in argv:
        errors.extend(check_notebook(Path(arg)))
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
