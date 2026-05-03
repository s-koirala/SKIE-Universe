"""Pre-commit guard enforcing the ADR-0013 §4 non-loss mandate.

Fails-closed on any staged deletion under the protected paths defined by
ADR-0013 §4.3, unless BOTH:
  1. The env var `SKIE_ALLOW_NON_LOSS_DELETION=1` is set.
  2. The commit message body contains a `# justify:` line.

This is the minimal first-pass implementation per Round-1 audit F-1-7
remediation; calibration of the protected-path regex (rename-detection,
column-change for append-only files) is tracked under
`P1-NON-LOSS-PRECOMMIT-GUARD-CALIBRATION`.

Wired into `.pre-commit-config.yaml` as a `repo: local` hook with
`stages: [pre-commit]` + `always_run: true` + `pass_filenames: false`.
The `always_run: true` flag is intentional (per Round-2 audit R-2-12):
the hook scans `git diff --cached` regardless of which files pre-commit
reports as changed, since deletion can co-occur with any change. Empty
commits (`git commit --allow-empty`) invoke the hook; with no staged
deletions the hook returns 0.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

PROTECTED_PATH_PREFIXES: tuple[str, ...] = (
    "docs/audits/",
    "logs/reproducibility/",
    "logs/promotions/",
    "runs/",
    "artifacts/runs/",
    "research/01_hypothesis_register/",
    "ninjascript/strategies/",
)

OVERRIDE_ENV_VAR = "SKIE_ALLOW_NON_LOSS_DELETION"
JUSTIFY_PATTERN = re.compile(r"^# justify:", re.MULTILINE)


def staged_deletions() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "--diff-filter=D"],
        capture_output=True,
        text=True,
        check=True,
    )
    deletions: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == "D":
            deletions.append(parts[1])
    return deletions


def is_protected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES)


def commit_message_has_justify() -> bool:
    msg_path = Path(".git/COMMIT_EDITMSG")
    if not msg_path.exists():
        return False
    return bool(JUSTIFY_PATTERN.search(msg_path.read_text(encoding="utf-8")))


def main() -> int:
    deletions = staged_deletions()
    protected_deletions = [p for p in deletions if is_protected(p)]
    if not protected_deletions:
        return 0

    override_env = os.environ.get(OVERRIDE_ENV_VAR) == "1"
    has_justify = commit_message_has_justify()
    if override_env and has_justify:
        sys.stderr.write(
            f"[non-loss-guard] override active: {OVERRIDE_ENV_VAR}=1 + commit "
            f"message contains '# justify:'\n"
            f"[non-loss-guard] permitting deletion of {len(protected_deletions)} "
            f"protected path(s):\n"
        )
        for p in protected_deletions:
            sys.stderr.write(f"  - {p}\n")
        return 0

    sys.stderr.write(
        "[non-loss-guard] BLOCKED: ADR-0013 §4 non-loss mandate forbids "
        "deletion of protected paths.\n\n"
    )
    sys.stderr.write("Protected deletions detected:\n")
    for p in protected_deletions:
        sys.stderr.write(f"  - {p}\n")
    sys.stderr.write(
        f"\nTo override (operator decision; record reason in commit message):\n"
        f"  1. Set env var: {OVERRIDE_ENV_VAR}=1\n"
        f"  2. Include a '# justify:' line in the commit message body\n\n"
        f"See [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md] §4.3.\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
