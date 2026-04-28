# Pre-launch check (ADR-0010 Layer 2): verify Windows Update will not
# auto-reboot this machine during a multi-hour run.
#
# Returns exit code:
#   0  = safe to launch (no pending restart, Active Hours covers run window)
#   2  = WARNING — pending restart scheduled but not imminent, OR Active Hours
#        does not cover the expected run window
#   3  = BLOCK — pending restart imminent; do not launch
#
# Emits a JSON report on stdout for the supervisor to parse.

param(
    # Round-2 Q-1-5 + R-6: expected runtime so we can verify Active
    # Hours covers the window. Default 22 hours (the upper end of the
    # H050 walk-forward estimate per the addendum).
    [int]$ExpectedRuntimeHours = 22
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
    status                   = "unknown"
    notes                    = @()
}

# Last boot time
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $report.last_boot_time = $os.LastBootUpTime.ToString("yyyy-MM-ddTHH:mm:sszzz")
} catch {
    $report.notes += "could not read Win32_OperatingSystem: $_"
}

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
    $report.status = "warn"
    $report.notes += "verdict: warn because Active Hours does not cover the expected run window"
    $exitCode = 2
} elseif ($null -eq $ahs) {
    $report.status = "warn"
    $report.notes += "verdict: warn because Active Hours is not configured"
    $exitCode = 2
} else {
    $report.status = "ok"
    $exitCode = 0
}

$report | ConvertTo-Json -Depth 4
exit $exitCode
