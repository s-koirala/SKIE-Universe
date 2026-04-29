#!/usr/bin/env bash
# P1-CFG-RELAUNCH-LOOP — outer loop that auto-relaunches the H050
# walk-forward orchestrator on any memory-related crash, using each
# prior run's cfg-checkpoint dir as the resume source for the next.
#
# Pragmatic alternative to per-cfg subprocess isolation: each
# invocation runs ~10-15 cfgs before fragmentation kills it; the
# outer loop's relaunch starts with a fresh process heap. The
# disk-persistent cfg-checkpoint pattern (P1-CFG-CHECKPOINT) bounds
# the work loss per crash to <=1 cfg. Total convergence is bounded
# by O(remaining_cfgs / cfgs_per_launch) ≈ 1-3 launches for the
# H050 16-NQ-cfg tail.
#
# Usage:
#   bash scripts/supervised_relaunch_loop.sh \
#       --symbols NQ \
#       --start-resume-run-id 338aac0a2d804e62b1ec54d36dba1a25 \
#       [--max-attempts 10]
#
# Exits 0 on a clean orchestrator rc=0 (success); 1 otherwise.

set -u
set -o pipefail

SYMBOLS=""
START_RESUME_RUN_ID=""
MAX_ATTEMPTS=10
HYPOTHESIS=H050
CONFIG="config/hypotheses/H050.yaml"
PER_LAUNCH_CAP_S=10800  # 3 hours per attempt (well below fragmentation wall)
EXPECTED_H=2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --symbols) SYMBOLS="$2"; shift 2 ;;
        --start-resume-run-id) START_RESUME_RUN_ID="$2"; shift 2 ;;
        --max-attempts) MAX_ATTEMPTS="$2"; shift 2 ;;
        --hypothesis) HYPOTHESIS="$2"; shift 2 ;;
        --config) CONFIG="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "$START_RESUME_RUN_ID" ]]; then
    echo "ERROR: --start-resume-run-id is required" >&2
    exit 2
fi

RESUME_RUN_ID="$START_RESUME_RUN_ID"

# BLAS pinning per ADR-0009.
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

for ATTEMPT in $(seq 1 "$MAX_ATTEMPTS"); do
    echo "================================================================="
    echo "Relaunch loop attempt $ATTEMPT / $MAX_ATTEMPTS"
    echo "Resume from run_id: $RESUME_RUN_ID"
    echo "Symbols filter:     ${SYMBOLS:-<all>}"
    echo "================================================================="

    ORCH_ARGS="--resume-hmm-cache $RESUME_RUN_ID --resume-cfg-checkpoint $RESUME_RUN_ID"
    if [[ -n "$SYMBOLS" ]]; then
        ORCH_ARGS="--symbols $SYMBOLS $ORCH_ARGS"
    fi

    uv run python scripts/supervised_run.py \
        --hypothesis "$HYPOTHESIS" \
        --config "$CONFIG" \
        --max-runtime-s "$PER_LAUNCH_CAP_S" \
        --expected-runtime-h "$EXPECTED_H" \
        --allow-preflight-warn \
        --orchestrator-args "$ORCH_ARGS"
    RC=$?

    # Find the most recent run_id (the run we just executed).
    LATEST_RUN_ID=$(ls -t "artifacts/runs/$HYPOTHESIS/" 2>/dev/null | head -1)

    if [[ "$RC" -eq 0 ]]; then
        echo "SUCCESS: orchestrator exited cleanly (rc=0). Stopping loop."
        echo "Final run_id: $LATEST_RUN_ID"
        exit 0
    fi

    echo "Attempt $ATTEMPT exited rc=$RC; latest run_id $LATEST_RUN_ID"

    # Use whichever run_id has the most cfg-checkpoints as the next
    # resume source. Usually the latest run, but if the latest crashed
    # before writing anything, fall back to the prior resume id.
    LATEST_CHECKPOINT_DIR="artifacts/runs/$HYPOTHESIS/$LATEST_RUN_ID/_cfg_checkpoints"
    if [[ -d "$LATEST_CHECKPOINT_DIR" ]]; then
        N_LATEST=$(ls "$LATEST_CHECKPOINT_DIR" 2>/dev/null | wc -l)
    else
        N_LATEST=0
    fi
    PRIOR_CHECKPOINT_DIR="artifacts/runs/$HYPOTHESIS/$RESUME_RUN_ID/_cfg_checkpoints"
    if [[ -d "$PRIOR_CHECKPOINT_DIR" ]]; then
        N_PRIOR=$(ls "$PRIOR_CHECKPOINT_DIR" 2>/dev/null | wc -l)
    else
        N_PRIOR=0
    fi
    echo "Checkpoint counts: latest=$N_LATEST prior=$N_PRIOR"

    # Consolidate latest checkpoints into a single resume dir if the
    # latest made progress; otherwise keep using the prior.
    if [[ "$N_LATEST" -gt 0 ]]; then
        # Copy latest cfg-checkpoints + HMM-fits onto the prior so
        # next attempt resumes from the union (ignore-existing so we
        # never overwrite a good pickle with a stale one).
        cp -n "$LATEST_CHECKPOINT_DIR"/*.pkl "$PRIOR_CHECKPOINT_DIR/" 2>/dev/null || true
        if [[ -d "artifacts/runs/$HYPOTHESIS/$LATEST_RUN_ID/_hmm_cache" ]]; then
            mkdir -p "artifacts/runs/$HYPOTHESIS/$RESUME_RUN_ID/_hmm_cache"
            cp -n "artifacts/runs/$HYPOTHESIS/$LATEST_RUN_ID/_hmm_cache"/*.pkl \
                  "artifacts/runs/$HYPOTHESIS/$RESUME_RUN_ID/_hmm_cache/" 2>/dev/null || true
        fi
        echo "Consolidated $LATEST_RUN_ID checkpoints + HMM fits into $RESUME_RUN_ID"
    fi

    # Loop with the same resume_run_id; it now has the union of all
    # prior checkpoints.
done

echo "FAILED: max-attempts $MAX_ATTEMPTS exhausted without rc=0"
exit 1
