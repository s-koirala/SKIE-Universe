# Pre-launch check (ADR-0010 Layer 2): verify Windows Update will not
# auto-reboot this machine during a multi-hour run.
#
# Returns exit code:
#   0  = safe to launch (no pending restart, Active Hours covers run window)
#   2  = WARNING - pending restart scheduled but not imminent, OR Active Hours
#        does not cover the expected run window
#   3  = BLOCK - pending restart imminent; do not launch
#
# Emits a JSON report on stdout for the supervisor to parse.
#
# P1-PREFLIGHT-SCRIPT-TIMEOUT (2026-04-30): if -OutputPath is provided,
# the script also writes the running report to disk after each major
# check section. On supervisor-side timeout, the partial JSON is then
# recoverable from disk rather than lost in stdout. The supervisor side
# is at scripts/supervised_run.py:_run_preflight which raises the
# subprocess timeout from 60s to 180s and reads the partial output on
# TimeoutExpired.

param(
    # Round-2 Q-1-5 + R-6: expected runtime so we can verify Active
    # Hours covers the window. Default 22 hours (the upper end of the
    # H050 walk-forward estimate per the addendum).
    [int]$ExpectedRuntimeHours = 22,

    # P1-PREFLIGHT-SCRIPT-TIMEOUT (2026-04-30): file path to write
    # incremental JSON. Empty string disables the partial-on-timeout
    # path; the report still goes to stdout at end.
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$report = @{
    ts                       = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    pending_restart          = $null
    active_hours_start       = $null
    active_hours_end         = $null
    active_hours_covers_run  = $null
    expected_runtime_hours   = $ExpectedRuntimeHours
    smart_active_hours_state = $null
    next_scheduled_restart   = $null
    last_boot_time           = $null
    status                   = "in-progress"
    progress_phase           = "init"
    notes                    = @()
}

# Helper: write the running report to disk if -OutputPath is set. Atomic
# via temp + Move-Item. The supervisor reads this file on TimeoutExpired.
function Write-PartialReport {
    param([hashtable]$Report, [string]$Path, [string]$Phase)
    if ([string]::IsNullOrEmpty($Path)) { return }
    try {
        $Report.progress_phase = $Phase
        $tmp = "$Path.tmp"
        $Report | ConvertTo-Json -Depth 4 | Set-Content -Path $tmp -Encoding UTF8
        Move-Item -Path $tmp -Destination $Path -Force
    } catch {
        # Partial-write failure is non-fatal; the final stdout dump is
        # still authoritative under the no-timeout happy path.
    }
}

Write-PartialReport -Report $report -Path $OutputPath -Phase "init"

# Last boot time
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $report.last_boot_time = $os.LastBootUpTime.ToString("yyyy-MM-ddTHH:mm:sszzz")
} catch {
    $report.notes += "could not read Win32_OperatingSystem: $_"
}
Write-PartialReport -Report $report -Path $OutputPath -Phase "after_last_boot_time"

# Pending-restart flag (CBS / Windows Update / Computer Rename)
$pending = $false
$pending_paths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
    "HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\JoinDomain",
    # Round-2 Q-1-13: Windows-11 OS-feature-update path
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\OSUpgrade"
)
foreach ($p in $pending_paths) {
    if (Test-Path $p) {
        $pending = $true
        $report.notes += "pending-restart marker present: $p"
    }
}
# PendingFileRenameOperations
try {
    $pfr = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -Name PendingFileRenameOperations -ErrorAction SilentlyContinue
    if ($pfr -and $pfr.PendingFileRenameOperations) {
        $pending = $true
        $report.notes += "PendingFileRenameOperations present"
    }
} catch {}
$report.pending_restart = $pending
Write-PartialReport -Report $report -Path $OutputPath -Phase "after_pending_restart"

# Active Hours: check policy override first, then user-set, then smart
$ahs = $null
$ahe = $null
try {
    $policy = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" -ErrorAction SilentlyContinue
    if ($policy -and ($policy.PSObject.Properties.Name -contains 'ActiveHoursStart')) {
        $ahs = $policy.ActiveHoursStart
        $ahe = $policy.ActiveHoursEnd
        $report.notes += "Active Hours sourced from Group Policy override"
    }
} catch {}
if ($null -eq $ahs) {
    try {
        $ah = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" -ErrorAction SilentlyContinue
        if ($ah) {
            $ahs = $ah.ActiveHoursStart
            $ahe = $ah.ActiveHoursEnd
            $report.smart_active_hours_state = $ah.SmartActiveHoursState
            if ($ah.SmartActiveHoursState -eq 1) {
                $report.notes += "Smart Active Hours is ENABLED; end-time is dynamic and may not match the static value"
            }
        } else {
            $report.notes += "Active Hours registry key not present (default policy may apply)"
        }
    } catch {
        $report.notes += "could not read Active Hours: $_"
    }
}
$report.active_hours_start = $ahs
$report.active_hours_end   = $ahe
Write-PartialReport -Report $report -Path $OutputPath -Phase "after_active_hours"

# P1-WAKE-LOCK-BYPASS-INVESTIGATION (2026-04-30): Windows-Update pause
# state. Read both the Settings-UI path (PauseUpdatesExpiryTime) and
# the Group-Policy path (PauseFeatureUpdatesEndTime / PauseQualityUpdatesEndTime).
# Q-1-7 fix: parse the timestamp and check that the pause genuinely
# covers (now + ExpectedRuntimeHours) — not just non-null.
$report.wu_paused_until = $null
$report.wu_pause_covers_run = $null
try {
    $pause_settings = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" -Name PauseUpdatesExpiryTime -ErrorAction SilentlyContinue
    $pause_policy = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" -Name PauseFeatureUpdatesEndTime -ErrorAction SilentlyContinue
    $candidate = $null
    if ($pause_settings -and $pause_settings.PauseUpdatesExpiryTime) {
        $candidate = $pause_settings.PauseUpdatesExpiryTime
        $report.notes += "WU pause (Settings UI): $candidate"
    }
    if ($pause_policy -and $pause_policy.PauseFeatureUpdatesEndTime) {
        # Prefer the policy path if both are set (it's the enforcement layer).
        $candidate = $pause_policy.PauseFeatureUpdatesEndTime
        $report.notes += "WU pause (Group Policy): $candidate"
    }
    if ($candidate) {
        $report.wu_paused_until = $candidate
        # Parse as UTC; expects "yyyy-MM-ddTHH:mm:ssZ" but tolerates
        # legacy local-time strings via fallback.
        $parsed_utc = $null
        try {
            $parsed_utc = [DateTime]::ParseExact(
                $candidate,
                "yyyy-MM-ddTHH:mm:ssZ",
                $null,
                [System.Globalization.DateTimeStyles]::AssumeUniversal -bor
                    [System.Globalization.DateTimeStyles]::AdjustToUniversal
            )
        } catch {
            try {
                $parsed_utc = [DateTime]::Parse($candidate).ToUniversalTime()
                $report.notes += "WU pause expiry parsed via fallback (non-canonical format): $candidate"
            } catch {
                $report.notes += "WU pause expiry could not be parsed: $candidate"
            }
        }
        if ($null -ne $parsed_utc) {
            $required_end_utc = (Get-Date).ToUniversalTime().AddHours($ExpectedRuntimeHours)
            $report.wu_pause_covers_run = ($parsed_utc -gt $required_end_utc)
            if (-not $report.wu_pause_covers_run) {
                $hours_short = ($required_end_utc - $parsed_utc).TotalHours
                $report.notes += "WU pause expires before the run window ends; short by $([math]::Round($hours_short,2)) h"
            }
        }
    }
} catch {}
Write-PartialReport -Report $report -Path $OutputPath -Phase "after_wu_pause"

# Round-2 Q-1-5 + R-6: does the next $ExpectedRuntimeHours fit
# within Active Hours? Returns null if AH is not set; true if the
# whole run window is inside AH; false if any part falls outside.
$covers = $null
if ($null -ne $ahs -and $null -ne $ahe) {
    $now = Get-Date
    $now_h = $now.Hour
    # Active Hours wraps if end < start (e.g. start=22, end=6 spans midnight)
    $window_size = if ($ahe -gt $ahs) { $ahe - $ahs } else { 24 + $ahe - $ahs }
    if ($ExpectedRuntimeHours -gt $window_size) {
        $covers = $false
        $report.notes += "expected runtime $ExpectedRuntimeHours h exceeds Active Hours window of $window_size h"
    } else {
        # Check if the window starting from now stays inside AH for $ExpectedRuntimeHours.
        # If now is outside AH, we will exit AH before reaching it; treat as not-covered.
        $now_in_ah = if ($ahe -gt $ahs) {
            ($now_h -ge $ahs) -and ($now_h -lt $ahe)
        } else {
            ($now_h -ge $ahs) -or ($now_h -lt $ahe)
        }
        if (-not $now_in_ah) {
            $covers = $false
            $report.notes += "current hour $now_h is outside Active Hours [$ahs, $ahe); run starts in a maintenance window"
        } else {
            # We're inside AH. Compute remaining hours until AH end.
            $remaining = if ($ahe -gt $ahs) { $ahe - $now_h } else {
                if ($now_h -ge $ahs) { (24 - $now_h) + $ahe } else { $ahe - $now_h }
            }
            $covers = $remaining -ge $ExpectedRuntimeHours
            if (-not $covers) {
                $report.notes += "only $remaining h remain in Active Hours; expected runtime $ExpectedRuntimeHours h would extend past AH end"
            }
        }
    }
}
$report.active_hours_covers_run = $covers

# Verdict
if ($pending) {
    $report.status = "block"
    $exitCode = 3
} elseif ($null -ne $covers -and -not $covers) {
    # If WU is paused AND the parsed pause-expiry exceeds (now + run window), downgrade to ok.
    # Q-1-7 fix: require validated coverage, not merely non-null pause string.
    if ($report.wu_pause_covers_run -eq $true) {
        $report.status = "ok"
        $report.notes += "verdict: ok despite AH coverage gap because WU pause is verified to cover the run window (until $($report.wu_paused_until))"
        $exitCode = 0
    } else {
        $report.status = "warn"
        $report.notes += "verdict: warn because Active Hours does not cover the expected run window AND no validated WU pause covers the window"
        $exitCode = 2
    }
} elseif ($null -eq $ahs) {
    $report.status = "warn"
    $report.notes += "verdict: warn because Active Hours is not configured"
    $exitCode = 2
} else {
    $report.status = "ok"
    $exitCode = 0
}

$report.progress_phase = "done"
Write-PartialReport -Report $report -Path $OutputPath -Phase "done"

$report | ConvertTo-Json -Depth 4
exit $exitCode
