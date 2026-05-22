# Worktree cleanup with ADR-0013 §4.1 non-loss preservation.
# Generated 2026-05-22 via audit-remediate-loop (R1 BLOCK, R2 BLOCK, R3 remediation).
#
# Audit trail: docs/audits/audit_trail_2026-05-22_worktree-cleanup.md
# Non-loss-guard interaction: scripts/_hooks/check_non_loss_deletion.py fires only on
#   `git diff --cached --diff-filter=D`; this script only ADDS files via Copy-IfMissing
#   and removes worktree directories (untracked from main HEAD's view), so the guard
#   correctly does not fire.
#
# Preserved §4.1 path classes (union of project guard + ADR-0013 §4.1 enumeration):
#   logs/reproducibility/   artifacts/runs/   runs/   reports/
#   docs/audits/   docs/decisions/   docs/research_notes/
#   research/01_hypothesis_register/   logs/promotions/   ninjascript/strategies/
#
# Excluded from preservation: artifacts/runs/<H>/<run_id>/_cfg_checkpoints/  (43 GB
#   crash-recovery pickles for run 31d23ecd...; NOT in §4.1 list).
#
# USAGE:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/worktree_cleanup_2026-05-22.ps1
#
# AFTER RUN: operator must `git add` + `git commit` the preserved files; see final prompt.

$ErrorActionPreference = 'Stop'
$root = "C:\Users\skoir\Documents\SKIE-Universe"
Set-Location $root
if ((Get-Location).Path -ne $root) { throw "cwd assertion failed" }

$worktreeRoot = ".claude\worktrees"
# justify: PID 27424 captured 2026-05-22 from `git worktree list --porcelain` showing the
# 2 locked agent worktrees (agent-a5482ade8d3642296 + agent-ac88b7403db9b2bab) sharing
# this PID. Refusal guard: if the OS still has a process with this PID alive, the
# agent may be mid-write and removal would corrupt state.
$lockedPid = 27424
# justify: worktree names enumerated from `.git/worktrees/*/locked` files at audit time.
$lockedWorktrees = @("agent-a5482ade8d3642296", "agent-ac88b7403db9b2bab")

$timestamp = Get-Date -Format 'yyyyMMddTHHmmss'
$preservationLogPath = "logs\worktree_cleanup_preservation_2026-05-22_$timestamp.log"

# --- pre-flight 1: no live process owning locked worktrees ---
if (Get-Process -Id $lockedPid -ErrorAction SilentlyContinue) {
    throw "PID $lockedPid is alive; refusing to touch its worktrees"
}

# --- pre-flight 2: no in-flight git operations on main ---
if ((Test-Path ".git\MERGE_HEAD") -or (Test-Path ".git\rebase-merge") -or (Test-Path ".git\CHERRY_PICK_HEAD")) {
    throw "in-progress merge/rebase/cherry-pick on main; resolve first"
}

# --- pre-flight 3: worktree root exists ---
if (-not (Test-Path $worktreeRoot)) {
    throw "$worktreeRoot does not exist; nothing to clean"
}

# --- pre-flight 4: dirty-worktree sweep ---
$dirty = @()
Get-ChildItem $worktreeRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $wtPath = $_.FullName
    if (Test-Path "$wtPath\.git") {
        # exclude ?? (untracked) AND !! (ignored); preserve M / A / D / R / C as dirty
        $st = & git -C $wtPath status --porcelain 2>$null | Where-Object { $_ -notmatch '^(\?\?|\!\!)' }
        if ($st) { $dirty += $_.Name }
    }
}
if ($dirty.Count -gt 0) { throw "dirty worktrees (uncommitted tracked changes): $($dirty -join ', ')" }

# --- preservation: union of §4.1-protected artifacts across all worktrees ---
$preservedCount = 0
$preservedBytes = 0L
$skippedExisting = 0
$missingSources = @()
$collisionsDifferent = @()
$preservationLog = @("=== run $timestamp ===")

function Copy-IfMissing($src, $dst) {
    if (-not (Test-Path $src)) {
        $script:missingSources += $src
        return
    }
    if (Test-Path $dst) {
        $script:skippedExisting++
        return
    }
    $dstParent = Split-Path $dst -Parent
    if ($dstParent -and -not (Test-Path $dstParent)) {
        New-Item -ItemType Directory -Force -Path $dstParent | Out-Null
    }
    # atomic: write to .tmp then rename
    $tmp = "$dst.cleanup_tmp"
    Copy-Item -LiteralPath $src -Destination $tmp -Force
    $srcLen = (Get-Item -LiteralPath $src).Length
    $tmpLen = (Get-Item -LiteralPath $tmp).Length
    if ($srcLen -ne $tmpLen) {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        throw "size mismatch on copy: $src ($srcLen B) -> $tmp ($tmpLen B)"
    }
    Move-Item -LiteralPath $tmp -Destination $dst -Force
    $script:preservedCount++
    $script:preservedBytes += $srcLen
    $script:preservationLog += "FILE $src -> $dst ($srcLen B)"
}

function Copy-IfMissing-WithCollisionDetect($src, $dst, $collisionDir) {
    # Used for ADRs where same-name-different-content is a real risk.
    # Multiple worktrees may carry distinct variants — append SHA prefix to filename
    # so every distinct variant survives. Same-content duplicates dedupe to one file.
    if (-not (Test-Path $src)) { return }
    if (Test-Path $dst) {
        $srcHash = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
        $dstHash = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
        if ($srcHash -ne $dstHash) {
            $name = Split-Path $dst -Leaf
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($name)
            $ext = [System.IO.Path]::GetExtension($name)
            $variantName = "${stem}_" + $srcHash.Substring(0, 16) + $ext
            $variant = Join-Path $collisionDir $variantName
            if (-not (Test-Path $collisionDir)) { New-Item -ItemType Directory -Force -Path $collisionDir | Out-Null }
            if (-not (Test-Path $variant)) {
                Copy-Item -LiteralPath $src -Destination $variant -Force
                $script:collisionsDifferent += "$src -> $variant (sha256 $($srcHash.Substring(0,16)); main sha256 $($dstHash.Substring(0,16)))"
                $script:preservationLog += "COLLISION $src -> $variant (main differs)"
                $script:preservedCount++
            } else {
                $script:skippedExisting++
            }
        } else {
            $script:skippedExisting++
        }
        return
    }
    Copy-IfMissing $src $dst
}

function Copy-RunDir($srcDir, $dstDir) {
    if (-not (Test-Path $srcDir)) { return }
    if (Test-Path $dstDir) {
        $script:skippedExisting++
        return
    }
    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
    # justify: PowerShell -ne is case-insensitive on Windows; matches NTFS case-insensitivity.
    Get-ChildItem -LiteralPath $srcDir -Force | Where-Object { $_.Name -ne '_cfg_checkpoints' } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $dstDir $_.Name) -Recurse -Force
    }
    $script:preservedCount++
    $sz = (Get-ChildItem -LiteralPath $srcDir -Recurse -File -ErrorAction SilentlyContinue |
           Where-Object { $_.FullName -notmatch '\\_cfg_checkpoints\\' } |
           Measure-Object -Property Length -Sum).Sum
    if ($sz) { $script:preservedBytes += $sz }
    $script:preservationLog += "DIR $srcDir -> $dstDir (_cfg_checkpoints excluded; $sz B)"
}

Write-Host "=== Preservation sweep ===" -ForegroundColor Cyan
$adrCollisionDir = "docs\decisions\_pending_renumber_from_worktrees"

Get-ChildItem $worktreeRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $wt = $_.Name
    $wtBase = $_.FullName
    Write-Host "  $wt" -ForegroundColor Gray

    # 1. logs/reproducibility/
    $reproDir = Join-Path $wtBase "logs\reproducibility"
    if (Test-Path $reproDir) {
        Get-ChildItem -LiteralPath $reproDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-IfMissing $_.FullName (Join-Path "logs\reproducibility" $_.Name)
        }
    }

    # 2. artifacts/runs/<H>/<run_id>/
    $runsDir = Join-Path $wtBase "artifacts\runs"
    if (Test-Path $runsDir) {
        Get-ChildItem -LiteralPath $runsDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $h = $_.Name
            Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $runId = $_.Name
                Copy-RunDir $_.FullName (Join-Path "artifacts\runs\$h" $runId)
            }
        }
    }

    # 3. runs/ (top-level; H053 stage sidecars per R2 finding)
    $runsTopDir = Join-Path $wtBase "runs"
    if (Test-Path $runsTopDir) {
        Get-ChildItem -LiteralPath $runsTopDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $rel = $_.FullName.Substring($wtBase.Length + 1)
            Copy-IfMissing $_.FullName $rel
        }
    }

    # 4. reports/ (H053 disposition memos per R2 finding)
    $reportsDir = Join-Path $wtBase "reports"
    if (Test-Path $reportsDir) {
        Get-ChildItem -LiteralPath $reportsDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $rel = $_.FullName.Substring($wtBase.Length + 1)
            Copy-IfMissing $_.FullName $rel
        }
    }

    # 5. docs/audits/
    $auditsDir = Join-Path $wtBase "docs\audits"
    if (Test-Path $auditsDir) {
        Get-ChildItem -LiteralPath $auditsDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-IfMissing $_.FullName (Join-Path "docs\audits" $_.Name)
        }
    }

    # 6. docs/decisions/ — ADRs may collide on filename
    $decDir = Join-Path $wtBase "docs\decisions"
    if (Test-Path $decDir) {
        Get-ChildItem -LiteralPath $decDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-IfMissing-WithCollisionDetect $_.FullName (Join-Path "docs\decisions" $_.Name) $adrCollisionDir
        }
    }

    # 7. docs/research_notes/
    $rnDir = Join-Path $wtBase "docs\research_notes"
    if (Test-Path $rnDir) {
        Get-ChildItem -LiteralPath $rnDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-IfMissing $_.FullName (Join-Path "docs\research_notes" $_.Name)
        }
    }

    # 8. research/01_hypothesis_register/
    $hrDir = Join-Path $wtBase "research\01_hypothesis_register"
    if (Test-Path $hrDir) {
        Get-ChildItem -LiteralPath $hrDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $rel = $_.FullName.Substring($wtBase.Length + 1)
            Copy-IfMissing $_.FullName $rel
        }
    }

    # 9. logs/promotions/
    $promDir = Join-Path $wtBase "logs\promotions"
    if (Test-Path $promDir) {
        Get-ChildItem -LiteralPath $promDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-IfMissing $_.FullName (Join-Path "logs\promotions" $_.Name)
        }
    }

    # 10. ninjascript/strategies/
    $njsDir = Join-Path $wtBase "ninjascript\strategies"
    if (Test-Path $njsDir) {
        Get-ChildItem -LiteralPath $njsDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-IfMissing $_.FullName (Join-Path "ninjascript\strategies" $_.Name)
        }
    }
}

$preservationLog += ""
$preservationLog += "=== summary ==="
$preservationLog += "preserved: $preservedCount files/dirs, $([math]::Round($preservedBytes/1MB,2)) MB"
$preservationLog += "skipped (already on main): $skippedExisting"
$preservationLog += "missing sources (expected, e.g., scientific_payload_sha256.txt absent): $($missingSources.Count)"
$preservationLog += "collision variants (same-name different-content; saved under _pending_renumber): $($collisionsDifferent.Count)"

Write-Host "  preserved $preservedCount files/dirs, $([math]::Round($preservedBytes/1MB,2)) MB" -ForegroundColor Green
Write-Host "  skipped $skippedExisting (already in main)" -ForegroundColor Gray
if ($collisionsDifferent.Count -gt 0) {
    Write-Host "  $($collisionsDifferent.Count) filename collisions with different content saved under $adrCollisionDir" -ForegroundColor Yellow
}
if (-not (Test-Path (Split-Path $preservationLogPath -Parent))) {
    New-Item -ItemType Directory -Force -Path (Split-Path $preservationLogPath -Parent) | Out-Null
}
$preservationLog | Out-File -FilePath $preservationLogPath -Encoding utf8

# --- git operations: switch to Continue preference ---
# justify: git emits non-error progress to stderr (e.g., "remote: ..." during push,
# "Preparing worktree" during remove). Under $ErrorActionPreference='Stop' these
# stderr writes become NativeCommandError and halt the script even though git's
# exit code is 0. From this point we explicitly check $LASTEXITCODE on every git call.
$ErrorActionPreference = 'Continue'

# --- push ecstatic-hellman (only branch not on origin) ---
Write-Host "=== Pushing ecstatic-hellman to origin ===" -ForegroundColor Cyan
$pushOut = & git push origin claude/ecstatic-hellman-937c44 2>&1
Write-Host ($pushOut | Out-String)
if ($LASTEXITCODE -ne 0) {
    throw "git push origin claude/ecstatic-hellman-937c44 failed (exit $LASTEXITCODE):`n$($pushOut | Out-String)"
}
$lsOut = & git ls-remote origin refs/heads/claude/ecstatic-hellman-937c44 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "git ls-remote failed (exit $LASTEXITCODE):`n$($lsOut | Out-String)"
}
$lsStr = ($lsOut | Out-String).Trim()
if ($lsStr -notmatch '^[0-9a-f]{40}\s') {
    throw "post-push ls-remote shows ecstatic-hellman branch absent or malformed: '$lsStr'"
}
$remoteSha = ($lsStr -split '\s')[0]
Write-Host "  ecstatic-hellman on origin: $remoteSha" -ForegroundColor Green

# --- unlock + remove locked worktrees ---
Write-Host "=== Removing locked agent worktrees ===" -ForegroundColor Cyan
foreach ($lockedWt in $lockedWorktrees) {
    $wtPath = Join-Path $worktreeRoot $lockedWt
    if (Test-Path $wtPath) {
        $unlockOut = & git worktree unlock $wtPath 2>&1
        if ($LASTEXITCODE -ne 0 -and ($unlockOut | Out-String) -notmatch 'not locked') {
            Write-Warning "unexpected unlock failure on ${lockedWt}: $($unlockOut | Out-String)"
        }
        $rmOut = & git worktree remove --force $wtPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "git worktree remove $lockedWt failed (exit $LASTEXITCODE):`n$($rmOut | Out-String)"
        }
        Write-Host "  removed $lockedWt" -ForegroundColor Green
    }
}

# --- remove remaining tracked worktrees (excluding main) ---
Write-Host "=== Removing tracked worktrees ===" -ForegroundColor Cyan
$mainPath = [System.IO.Path]::GetFullPath($root).Replace('\','/').TrimEnd('/').ToLower()
$lines = & git worktree list --porcelain
$wtPaths = $lines | Select-String '^worktree ' | ForEach-Object {
    ($_ -split ' ', 2)[1].Trim()
} | Where-Object {
    $norm = $_.Replace('\','/').TrimEnd('/').ToLower()
    $norm -ne $mainPath
}
$removedCount = 0
$removeFailures = @()
foreach ($wt in $wtPaths) {
    $rmOut = & git worktree remove --force $wt 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git worktree remove $wt failed (exit $LASTEXITCODE): $($rmOut | Out-String)"
        $removeFailures += $wt
    } else {
        $removedCount++
        Write-Host "  removed $wt" -ForegroundColor Green
    }
}
Write-Host "  $removedCount worktrees removed" -ForegroundColor Green

# --- remove orphan stub directories (with §4.1 guard) ---
Write-Host "=== Removing orphan stub directories ===" -ForegroundColor Cyan
$trackedSet = @{}
& git worktree list --porcelain | Select-String '^worktree ' | ForEach-Object {
    $p = ($_ -split ' ', 2)[1].Trim().Replace('/','\').ToLower()
    $trackedSet[$p] = $true
}
$protectedRegex = '\\(logs\\reproducibility|artifacts\\runs|runs|reports|docs\\audits|docs\\decisions|docs\\research_notes|research\\01_hypothesis_register|logs\\promotions|ninjascript\\strategies)\\'
$orphanRemoved = 0
Get-ChildItem $worktreeRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $p = $_.FullName.ToLower()
    if (-not $trackedSet.ContainsKey($p)) {
        $protectedHere = Get-ChildItem -LiteralPath $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match $protectedRegex }
        if ($protectedHere) {
            Write-Warning "orphan stub $($_.Name) holds protected files; refusing to delete"
            $protectedHere | ForEach-Object { Write-Warning "  $($_.FullName)" }
        } else {
            Remove-Item -LiteralPath $_.FullName -Recurse -Force
            $orphanRemoved++
            Write-Host "  removed orphan stub $($_.Name)" -ForegroundColor Green
        }
    }
}
Write-Host "  $orphanRemoved orphan stubs removed" -ForegroundColor Green

& git worktree prune

# --- final summary + operator-action prompt ---
Write-Host ""
Write-Host "=== CLEANUP COMPLETE ===" -ForegroundColor Cyan
Write-Host "  preserved: $preservedCount files/dirs ($([math]::Round($preservedBytes/1MB,2)) MB)"
Write-Host "  worktrees removed: $($removedCount + $lockedWorktrees.Count) (including 2 locked)"
Write-Host "  orphan stubs removed: $orphanRemoved"
if ($removeFailures.Count -gt 0) {
    Write-Host "  REMOVE FAILURES: $($removeFailures.Count) — investigate" -ForegroundColor Red
    $removeFailures | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
}
if ($collisionsDifferent.Count -gt 0) {
    Write-Host "  $($collisionsDifferent.Count) ADR/file-name collisions saved under $adrCollisionDir — REVIEW + RENUMBER" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "NEXT STEPS (operator action required):" -ForegroundColor Yellow
Write-Host "  1. Review preservation log: cat $preservationLogPath"
Write-Host "  2. Inspect new files: git status"
Write-Host "  3. Stage + commit per ADR-0013 §4.1 non-loss:"
Write-Host "       git add artifacts/runs/ logs/reproducibility/ runs/ reports/ docs/audits/ docs/decisions/ docs/research_notes/ research/01_hypothesis_register/"
Write-Host "       git commit -m 'chore: preserve §4.1 artifacts from worktree cleanup (2026-05-22)'"
Write-Host "  4. If ADR collisions exist, review _pending_renumber/ and resolve before commit."
