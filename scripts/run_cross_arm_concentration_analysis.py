"""Cross-arm early-2020 concentration replication test.

Per CLAUDE.md Phase O.7.4 §"Cross-cutting empirical synthesis" + iter 4
follow-up: does the H062 +208.8% concentration in early-2020 (Jan-May
2020 at km=1.5 + Sharpe 1.76-3.97) generalize to OTHER project
hypotheses (H060 cross-futures TSMOM; H062 v1 in basket aggregate),
or is it H062-cell-specific?

Approach: load each arm's sidecar, extract per_fold[*].test_dates +
mppm_oos, build chronological cumulative-log-return curve, compute the
contribution of Q1-H1 2020 vs rest of OOS window.

Hypothesis: if the early-2020 concentration replicates across BOTH
H060 (daily-cadence TSMOM) AND H062 (intraday Donchian breakout), the
finding is REGIME-SPECIFIC (project-wide); if H060 is uniform across
years, the H062 finding is signal-class-specific.

Output: comparison table + sidecar.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("cross_arm_concentration")


def _parse_date(ts_str: str) -> pd.Timestamp:
    return pd.Timestamp(str(ts_str), tz="UTC") if "+" in str(ts_str) else pd.Timestamp(str(ts_str))


def _analyze_arm(
    arm_id: str, sidecar_path: Path, *, per_symbol: bool = False,
) -> dict[str, Any]:
    """Extract per-fold (test_end_date, mppm_oos) timeline; compute
    early-2020 vs rest concentration."""
    sc = json.load(open(sidecar_path, encoding="utf-8"))
    per_fold = sc.get("per_fold", [])
    if not per_fold:
        return {"arm_id": arm_id, "error": "no per_fold records"}

    # Build (test_end_date, mppm_oos, symbol) timeline
    folds: list[dict[str, Any]] = []
    for f in per_fold:
        td = f.get("test_dates", [])
        if len(td) < 2:
            continue
        try:
            test_start = _parse_date(td[0])
            test_end = _parse_date(td[1])
        except Exception:  # noqa: BLE001
            continue
        mppm = f.get("mppm_oos")
        if mppm is None or (isinstance(mppm, float) and not np.isfinite(mppm)):
            continue
        folds.append({
            "test_start": test_start, "test_end": test_end,
            "mppm_oos": float(mppm),
            "symbol": f.get("symbol", "BASKET"),
            "sr_arm": f.get("sr_arm_annualised"),
            "sr_bench": f.get("sr_bench_annualised"),
        })
    folds.sort(key=lambda x: x["test_end"])

    early_2020_cutoff = pd.Timestamp("2020-06-30", tz="UTC")
    summary: dict[str, dict[str, Any]] = {}
    symbols = sorted({f["symbol"] for f in folds}) if per_symbol else ["ALL"]
    for sym in symbols:
        sym_folds = [f for f in folds if (not per_symbol or f["symbol"] == sym)]
        if not sym_folds:
            continue
        mppms = np.array([f["mppm_oos"] for f in sym_folds], dtype=float)
        # Cumulative log-return treats each fold's MPPM as 1-period contribution
        # (MPPM_oos is annualised log-wealth per Goetzmann-Ingersoll-Spiegel-Welch
        # 2007; fold-period is ~3 months; this is a proxy — exact requires
        # fold-period log-return which isn't in sidecar). Use sum-of-MPPMs as
        # a proxy ranking metric.
        cum = float(mppms.sum())

        early_folds = [f for f in sym_folds if f["test_end"] <= early_2020_cutoff]
        late_folds = [f for f in sym_folds if f["test_end"] > early_2020_cutoff]
        early_mppm = sum(f["mppm_oos"] for f in early_folds)
        late_mppm = sum(f["mppm_oos"] for f in late_folds)
        early_share = (early_mppm / cum * 100) if cum != 0 else float("nan")

        summary[sym] = {
            "n_folds_total": len(sym_folds),
            "n_folds_early_2020": len(early_folds),
            "n_folds_late": len(late_folds),
            "first_test_end": str(sym_folds[0]["test_end"].date()),
            "last_test_end": str(sym_folds[-1]["test_end"].date()),
            "cum_mppm_oos_full": cum,
            "cum_mppm_oos_early_2020": early_mppm,
            "cum_mppm_oos_late": late_mppm,
            "early_2020_share_pct": early_share,
            "n_folds_positive": int((mppms > 0).sum()),
            "median_mppm": float(np.median(mppms)),
            "mean_mppm": float(mppms.mean()),
        }
    return {"arm_id": arm_id, "n_folds": len(folds), "summary": summary}


def main() -> int:
    out_dir = (
        _REPO_ROOT / "artifacts" / "runs" / "cross_arm_concentration"
        / f"v1_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    arms = [
        ("H060", _REPO_ROOT / "artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json", False),
        ("H062", _REPO_ROOT / "artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json", True),
    ]

    all_results = []
    for arm_id, p, per_sym in arms:
        if not p.exists():
            _log.warning("%s: sidecar missing at %s", arm_id, p)
            continue
        res = _analyze_arm(arm_id, p, per_symbol=per_sym)
        all_results.append(res)
        if "error" in res:
            _log.warning("%s: %s", arm_id, res["error"])
            continue
        for sym, s in res["summary"].items():
            _log.info(
                "%s%s: %d folds [%s -> %s]; early2020 %d folds = %.1f%% of cum_mppm (cum=%.3f early=%.3f late=%.3f)",
                arm_id,
                f"-{sym}" if sym != "ALL" else "",
                s["n_folds_total"], s["first_test_end"], s["last_test_end"],
                s["n_folds_early_2020"], s["early_2020_share_pct"],
                s["cum_mppm_oos_full"], s["cum_mppm_oos_early_2020"], s["cum_mppm_oos_late"],
            )

    payload = {
        "experiment": "cross_arm_early_2020_concentration_replication",
        "early_2020_cutoff": "2020-06-30",
        "arms_analyzed": [r["arm_id"] for r in all_results],
        "results": all_results,
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sidecar.json"
    sb = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sb)
    sha = hashlib.sha256(sb).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    print()
    print("=" * 110)
    print("CROSS-ARM EARLY-2020 CONCENTRATION REPLICATION")
    print(f"  cutoff: 2020-06-30 (early-2020 = test_end <= cutoff; late = after)")
    print(f"  sidecar: {sidecar_path}")
    print(f"  sha256:  {sha}")
    print("=" * 110)
    print(f"{'arm':<10} {'n_folds':>9} {'early_n':>9} {'early_share%':>14} {'cum_mppm':>11} {'med_mppm':>11} {'n_pos':>7}")
    for r in all_results:
        if "error" in r: continue
        for sym, s in r["summary"].items():
            label = r["arm_id"] + (f"-{sym}" if sym != "ALL" else "")
            print(
                f"{label:<10} {s['n_folds_total']:>9} {s['n_folds_early_2020']:>9} "
                f"{s['early_2020_share_pct']:>+12.1f}% {s['cum_mppm_oos_full']:>+10.3f} "
                f"{s['median_mppm']:>+10.3f} {s['n_folds_positive']:>7}"
            )
    print("=" * 110)
    print()
    print("INTERPRETATION GUIDE:")
    print("  early_share% > 60% in BOTH H060 + H062-* → regime-specific (project-wide early-2020 dependency)")
    print("  early_share% > 60% in H062 only      → H062-cell-specific (Donchian-breakout-on-COVID artifact)")
    print("  early_share% < 30% in H060          → H060 has distributed edge; H062 finding is signal-class")
    return 0


if __name__ == "__main__":
    sys.exit(main())
