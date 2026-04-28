"""Supervised launch wrapper for multi-hour H050 walk-forward runs.

Implements [ADR-0010](../docs/decisions/ADR-0010-multi-hour-run-process-protection.md)
Layer 2 (programmatic pre-launch verification) + Layer 4 (resource
telemetry + external-kill detection).

Spawns ``scripts/run_walk_forward.py`` as a subprocess and:

  1. Runs ``scripts/preflight/check_windows_update.ps1`` first; refuses
     to launch if the preflight returns BLOCK (exit 3).
  2. Captures the orchestrator's stdout (JSON log stream) to
     ``logs/walk_forward_runs/h050_prod_run_<DATE>.log``.
  3. Samples the subprocess's RSS / CPU% / thread count / latest
     PROGRESS line every ``--telemetry-interval-s`` seconds and
     appends to ``logs/walk_forward_runs/h050_prod_run_<DATE>.supervisor.jsonl``.
  4. On subprocess exit, classifies the exit:
       - clean exit (rc=0 + final ``PROGRESS run done``): success.
       - clean failure (rc != 0 + final ``PROGRESS <phase> failed``):
         in-process exception; the failed marker carries the exc_type.
       - external kill (rc != 0 + no failed marker; latest PROGRESS is
         a ``start``): orphaned start indicates the OS killed the
         process between the start and its done/failed (the
         prod-run-2 failure mode).
  5. Writes a summary at ``logs/walk_forward_runs/h050_prod_run_<DATE>.summary.json``
     with the classification + last 50 lines of the orchestrator log.

Per ADR-0010, this wrapper is the canonical launch path for any
walk-forward run expected to exceed one hour. Direct invocation of
``scripts/run_walk_forward.py`` is permitted for short / interactive
runs (the wake-lock still engages from ``__main__``) but does not get
preflight verification or resource telemetry.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parents[1]  # paths-guard: allow (supervisor wrapper script; spawns subprocess relative to repo root, not loaded as a project module)
_DEFAULT_TELEMETRY_INTERVAL_S = 30.0
_DEFAULT_LOG_DIR = _REPO_ROOT / "logs" / "walk_forward_runs"
# Round-2 Q-1-3: max wall-clock cap. The H050 run is estimated 12-22 hr
# per the addendum; 36 hr is a generous ceiling that catches the
# catastrophic-hang case (e.g. wake-lock prevents OS reboot but a
# library deadlock blocks the main thread indefinitely).
_DEFAULT_MAX_RUNTIME_S = 36.0 * 3600.0
# Round-2 Q-1-5 + R-6: default expected runtime for the Active-Hours
# coverage check.
_DEFAULT_EXPECTED_RUNTIME_H = 22


def _ts_tag() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%dT%H%M%S")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _run_preflight(
    preflight_path: Path,
    expected_runtime_h: int = _DEFAULT_EXPECTED_RUNTIME_H,
) -> tuple[int, dict[str, Any] | None]:
    """Returns (exit_code, parsed_json_or_None).

    Round-2 audit-remediate fixes:

    - Q-1-4: missing-script and exception paths now return rc=2 (warn)
      rather than rc=0 (silently permissive). The supervisor's
      classification at the call site treats rc=2 as "refuse to launch
      unless `--allow-preflight-warn`".
    - R-4: non-Windows hosts skip the PowerShell invocation entirely
      and return rc=0 with `status=non-windows-skip` (the wake-lock
      itself is also a no-op on non-Windows; no protection needed).
    - Q-1-5 + R-6: passes `expected_runtime_h` so the .ps1 script can
      check whether Active Hours covers the run window.
    """
    if sys.platform != "win32":
        return 0, {
            "status": "non-windows-skip",
            "reason": f"non-Windows host ({sys.platform}); wake-lock + preflight are Windows-only",
        }
    if not preflight_path.exists():
        return 2, {
            "status": "warn",
            "reason": f"preflight script not found at {preflight_path}",
        }
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(preflight_path),
                "-ExpectedRuntimeHours",
                str(expected_runtime_h),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {
                "status": "unparseable",
                "raw_stdout": proc.stdout,
                "raw_stderr": proc.stderr,
            }
        return proc.returncode, payload
    except Exception as exc:  # noqa: BLE001
        return 2, {"status": "warn", "error": repr(exc)}


def _sample_process_telemetry(pid: int) -> dict[str, Any]:
    """Capture RSS / CPU% / thread count / num_handles for a process
    and its children. Best-effort; missing fields default to None."""
    try:
        import psutil  # local import; supervisor optional dep
    except ImportError:
        return {"error": "psutil not installed; install with `uv pip install psutil`"}

    try:
        proc = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
        return {"error": f"process {pid} not accessible: {exc!r}"}

    sample: dict[str, Any] = {"pid": pid, "ts": _dt.datetime.now().isoformat()}
    try:
        with proc.oneshot():
            sample["status"] = proc.status()
            sample["rss_bytes"] = proc.memory_info().rss
            sample["vms_bytes"] = proc.memory_info().vms
            sample["num_threads"] = proc.num_threads()
            try:
                sample["cpu_percent"] = proc.cpu_percent(interval=None)
            except Exception:
                sample["cpu_percent"] = None
            try:
                sample["create_time"] = proc.create_time()
            except Exception:
                pass
        # Include children if any (uv may spawn subprocess; the actual
        # python process is a child of `uv.exe`).
        children = proc.children(recursive=True)
        if children:
            sample["children"] = [
                {
                    "pid": c.pid,
                    "name": c.name(),
                    "status": c.status(),
                    "rss_bytes": c.memory_info().rss,
                    "num_threads": c.num_threads(),
                    "cpu_percent": c.cpu_percent(interval=None),
                }
                for c in children
                if c.is_running()
            ]
    except Exception as exc:  # noqa: BLE001
        sample["error"] = repr(exc)
    return sample


def _classify_exit(rc: int, last_progress_lines: list[str]) -> dict[str, Any]:
    """Classify subprocess exit per the supervisor docstring."""
    has_run_done = any("PROGRESS run done" in ln for ln in last_progress_lines)
    has_failed = any(" failed elapsed=" in ln for ln in last_progress_lines)
    last_start_phases = [
        ln for ln in last_progress_lines if " start " in ln or ln.endswith(" start")
    ]
    last_done_or_failed = [
        ln
        for ln in last_progress_lines
        if " done elapsed=" in ln or " failed elapsed=" in ln
    ]

    if rc == 0 and has_run_done:
        return {"classification": "clean_exit_success", "rc": rc}
    if rc != 0 and has_failed:
        return {
            "classification": "clean_exit_python_exception",
            "rc": rc,
            "note": "PROGRESS failed marker present; exc_type in marker",
        }
    if rc != 0 and not has_failed:
        n_orphan_starts = max(0, len(last_start_phases) - len(last_done_or_failed))
        return {
            "classification": "external_kill_or_segfault",
            "rc": rc,
            "n_orphan_starts": n_orphan_starts,
            "note": (
                "Subprocess exited non-zero with NO PROGRESS failed marker. "
                "Likely external termination (OS reboot / OOM / SIGKILL) "
                "or native segfault. Inspect Windows System Event Log for "
                "Kernel-Power Event 109 (Windows Update reboot) or "
                "Application Event 1001 (BugCheck / process crash)."
            ),
        }
    return {"classification": "ambiguous", "rc": rc}


def _tail_lines(path: Path, n: int = 50) -> list[str]:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Supervised launch for the H050 walk-forward orchestrator (ADR-0010 Layers 2 + 4)."
    )
    ap.add_argument("--hypothesis", required=True, help="Hypothesis ID to forward to the orchestrator.")
    ap.add_argument("--config", required=True, type=Path, help="Hypothesis YAML config path.")
    ap.add_argument(
        "--telemetry-interval-s",
        type=float,
        default=_DEFAULT_TELEMETRY_INTERVAL_S,
        help=f"Sampling interval for RSS/CPU telemetry. Default {_DEFAULT_TELEMETRY_INTERVAL_S}s.",
    )
    ap.add_argument(
        "--log-dir",
        type=Path,
        default=_DEFAULT_LOG_DIR,
        help=f"Directory for orchestrator log + supervisor telemetry + summary. Default {_DEFAULT_LOG_DIR}.",
    )
    ap.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip the Windows-Update preflight check. Default: enforce.",
    )
    ap.add_argument(
        "--allow-preflight-warn",
        action="store_true",
        help="Launch even if preflight returns WARN (exit 2). Default: refuse.",
    )
    ap.add_argument(
        "--orchestrator-args",
        type=str,
        default="",
        help="Additional args to forward to scripts/run_walk_forward.py (single-quoted string).",
    )
    ap.add_argument(
        "--max-runtime-s",
        type=float,
        default=_DEFAULT_MAX_RUNTIME_S,
        help=(
            f"Round-2 Q-1-3: max wall-clock cap. If the orchestrator "
            f"is still running after this many seconds, the supervisor "
            f"calls proc.terminate() then proc.kill() with a 30-sec grace "
            f"period and classifies as 'supervisor_max_runtime_exceeded'. "
            f"Default {_DEFAULT_MAX_RUNTIME_S:.0f}s ({_DEFAULT_MAX_RUNTIME_S/3600:.0f} hours)."
        ),
    )
    ap.add_argument(
        "--expected-runtime-h",
        type=int,
        default=_DEFAULT_EXPECTED_RUNTIME_H,
        help=(
            "Round-2 Q-1-5 + R-6: passed to the preflight script so "
            "it can check whether Active Hours covers the run window."
        ),
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    args.log_dir.mkdir(parents=True, exist_ok=True)

    tag = _ts_tag()
    base = args.log_dir / f"h050_prod_run_{tag}"
    log_path = base.with_suffix(".log")
    telemetry_path = base.with_suffix(".supervisor.jsonl")
    summary_path = base.with_suffix(".summary.json")
    preflight_path = _REPO_ROOT / "scripts" / "preflight" / "check_windows_update.ps1"
    preflight_report_path = base.with_suffix(".preflight.json")

    print(f"[supervisor] launching at {tag}", flush=True)
    print(f"[supervisor]   log:        {log_path}", flush=True)
    print(f"[supervisor]   telemetry:  {telemetry_path}", flush=True)
    print(f"[supervisor]   summary:    {summary_path}", flush=True)

    # --- Preflight --------------------------------------------------
    if not args.skip_preflight:
        rc, report = _run_preflight(
            preflight_path, expected_runtime_h=args.expected_runtime_h
        )
        if report is not None:
            _atomic_write_json(preflight_report_path, report)
        print(f"[supervisor] preflight rc={rc} status={report.get('status') if report else 'n/a'}", flush=True)
        if rc == 3:
            print("[supervisor] BLOCKED by preflight; refusing to launch.", flush=True)
            print(f"[supervisor] preflight report at {preflight_report_path}", flush=True)
            return 3
        if rc == 2 and not args.allow_preflight_warn:
            print(
                "[supervisor] WARN from preflight; refusing to launch. "
                "Pass --allow-preflight-warn to override.",
                flush=True,
            )
            print(f"[supervisor] preflight report at {preflight_report_path}", flush=True)
            return 2

    # --- Spawn orchestrator -----------------------------------------
    orchestrator_cmd = [
        sys.executable,
        str(_REPO_ROOT / "scripts" / "run_walk_forward.py"),
        "--hypothesis",
        args.hypothesis,
        "--config",
        str(args.config),
    ]
    if args.orchestrator_args.strip():
        orchestrator_cmd.extend(args.orchestrator_args.strip().split())

    env = os.environ.copy()
    # Propagate ADR-0009 BLAS pinning if the supervisor was launched
    # without it; the orchestrator's correctness depends on these.
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        env.setdefault(k, "1")

    log_handle = open(log_path, "w", encoding="utf-8", buffering=1)
    print(f"[supervisor] orchestrator cmd: {' '.join(orchestrator_cmd)}", flush=True)
    print(f"[supervisor] BLAS env: OMP={env['OMP_NUM_THREADS']} MKL={env['MKL_NUM_THREADS']} OPENBLAS={env['OPENBLAS_NUM_THREADS']}", flush=True)

    proc = subprocess.Popen(
        orchestrator_cmd,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(_REPO_ROOT),
    )
    print(f"[supervisor] orchestrator pid={proc.pid}", flush=True)

    # --- Telemetry loop ---------------------------------------------
    telemetry_handle = open(telemetry_path, "w", encoding="utf-8", buffering=1)
    loop_start = time.time()
    max_runtime_exceeded = False
    try:
        while True:
            try:
                rc = proc.wait(timeout=args.telemetry_interval_s)
                # Subprocess exited within the interval; final rc captured.
                break
            except subprocess.TimeoutExpired:
                # Round-2 Q-1-3: enforce max wall-clock cap.
                elapsed_s = time.time() - loop_start
                if elapsed_s > args.max_runtime_s:
                    print(
                        f"[supervisor] max runtime {args.max_runtime_s:.0f}s "
                        f"exceeded (elapsed={elapsed_s:.0f}s); terminating "
                        f"orchestrator pid={proc.pid}",
                        flush=True,
                    )
                    max_runtime_exceeded = True
                    proc.terminate()
                    try:
                        rc = proc.wait(timeout=30.0)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        rc = proc.wait(timeout=10.0)
                    break
                sample = _sample_process_telemetry(proc.pid)
                # Append latest PROGRESS line for context.
                last_progress = [
                    ln
                    for ln in _tail_lines(log_path, n=20)
                    if '"PROGRESS' in ln
                ]
                if last_progress:
                    sample["latest_progress"] = last_progress[-1][:300]
                try:
                    telemetry_handle.write(json.dumps(sample, default=str) + "\n")
                    telemetry_handle.flush()
                except OSError as exc:
                    # Disk-full / permission-denied: degrade gracefully.
                    print(
                        f"[supervisor] WARN telemetry write failed: {exc!r}; "
                        f"continuing without telemetry",
                        flush=True,
                    )
    finally:
        telemetry_handle.close()
        log_handle.close()
        # Defensive: ensure subprocess is not left dangling on any
        # supervisor exit path.
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10.0)
            except subprocess.TimeoutExpired:
                proc.kill()

    # --- Classification + summary -----------------------------------
    final_tail = _tail_lines(log_path, n=200)
    final_progress = [ln for ln in final_tail if '"PROGRESS' in ln]
    classification = _classify_exit(rc, final_progress)
    if max_runtime_exceeded:
        # Override the heuristic classification with the explicit signal.
        classification = {
            "classification": "supervisor_max_runtime_exceeded",
            "rc": rc,
            "max_runtime_s": args.max_runtime_s,
            "note": (
                "Supervisor terminated the orchestrator after the configured "
                "--max-runtime-s ceiling. Classify as a hung process; "
                "inspect the latest PROGRESS line and telemetry to diagnose "
                "where the orchestrator stopped making progress."
            ),
        }
    summary = {
        "supervisor_ts": tag,
        "orchestrator_cmd": orchestrator_cmd,
        "orchestrator_rc": rc,
        "orchestrator_pid": proc.pid,
        "log_path": str(log_path),
        "telemetry_path": str(telemetry_path),
        "preflight_report_path": str(preflight_report_path) if preflight_report_path.exists() else None,
        "classification": classification,
        "n_progress_lines": len(final_progress),
        "tail_progress_lines": final_progress[-20:],
    }
    _atomic_write_json(summary_path, summary)

    print(f"[supervisor] orchestrator exited rc={rc}", flush=True)
    print(f"[supervisor] classification: {classification['classification']}", flush=True)
    if classification["classification"] != "clean_exit_success":
        note = classification.get("note", "")
        if note:
            print(f"[supervisor] note: {note}", flush=True)
    print(f"[supervisor] summary: {summary_path}", flush=True)
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
