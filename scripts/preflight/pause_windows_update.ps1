# P1-WAKE-LOCK-BYPASS-INVESTIGATION defense layer (2026-04-30):
# pause Windows Update for the duration of a multi-hour run.
#
# Motivation: per audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md
# F-1, the wake-lock (ES_SYSTEM_REQUIRED) is empirically insufficient
# on Windows 11 against UsoSvc / MoUsoCoreWorker enforcement-deadline
# reboots. The Round-1 quant audit (Q-1-2 disposition) framed H-B as
# "UsoSvc enforcement-deadline reboot path that does not require
# pre-reboot WU 19/20 events". Round-1 acceptance-criteria probe of
# Microsoft-Windows-WindowsUpdateClient/Operational for the
# 2026-04-29 20:14-20:16 window found Event 26 at 20:16:03 -- the
# same second as Kernel-Power Event 109. UsoSvc was active at the
# reboot instant, supporting H-B.
#
# This script writes PauseUpdatesExpiryTime to a future timestamp,
# pausing Windows Update auto-restart for the run window. Per
# https://learn.microsoft.com/en-us/windows/deployment/update/waas-pause-features
# the registry mechanism is documented and reversible at any time.
#
# Limits:
# - Requires admin privileges (HKLM write).
# - Maximum pause is 35 days per Microsoft policy; a 24-hour pause is
#   well within bounds.
# - User-initiated reboots, BSOD, hardware power loss are still out of
#   scope (per ADR-0010 §"Out-of-scope" Layer 1 forward-link Note).
#
# Usage:
#   powershell.exe -ExecutionPolicy Bypass -File scripts\preflight\pause_windows_update.ps1 -Hours 24
#   # Verify:
#   Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -Name PauseUpdatesExpiryTime
#   # Resume early (before expiry):
#   powershell.exe -ExecutionPolicy Bypass -File scripts\preflight\pause_windows_update.ps1 -Resume

param(
    [int]$Hours = 24,
    [switch]$Resume
)

$ErrorActionPreference = "Stop"

function Test-IsAdmin {
    $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $p = [System.Security.Principal.WindowsPrincipal]::new($id)
    return $p.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Host "ERROR: this script requires admin privileges (HKLM write). Run from an elevated PowerShell." -ForegroundColor Red
    exit 2
}

$key = "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"

if ($Resume) {
    try {
        # Settings-UI path
        Remove-ItemProperty -Path $key -Name PauseUpdatesExpiryTime -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $key -Name PauseFeatureUpdatesEndTime -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $key -Name PauseQualityUpdatesEndTime -ErrorAction SilentlyContinue
        # Group-Policy path (Q-1-4 fix)
        $policy_key = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
        if (Test-Path $policy_key) {
            Remove-ItemProperty -Path $policy_key -Name PauseFeatureUpdatesStartTime -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $policy_key -Name PauseFeatureUpdatesEndTime -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $policy_key -Name PauseQualityUpdatesStartTime -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $policy_key -Name PauseQualityUpdatesEndTime -ErrorAction SilentlyContinue
        }
        Write-Host "Windows Update pause cleared (Settings UI + Group Policy). Updates may resume at the next OS check." -ForegroundColor Green
        exit 0
    } catch {
        Write-Host "ERROR clearing pause: $_" -ForegroundColor Red
        exit 1
    }
}

if ($Hours -lt 1 -or $Hours -gt 840) {
    Write-Host "ERROR: -Hours must be between 1 and 840 (35 days)." -ForegroundColor Red
    exit 2
}

# Round-1 audit Q-1-3 fix: explicitly construct the expiry in UTC so
# the literal `Z` suffix in the format string is truthful. Previously
# `(Get-Date).AddHours()` returned LOCAL time and the appended `Z`
# mislabeled it as UTC; on a CT host this made a 24-hr pause genuinely
# only ~19 hr in UTC interpretation.
$expiry_utc = (Get-Date).ToUniversalTime().AddHours($Hours)
$expiry = $expiry_utc.ToString("yyyy-MM-ddTHH:mm:ssZ")
$policy_start_utc = (Get-Date).ToUniversalTime()
$policy_start_iso = $policy_start_utc.ToString("yyyy-MM-ddTHH:mm:ssZ")

# Round-1 audit Q-1-4 fix: write to BOTH the Settings-UI path (for
# operator visibility) AND the Group-Policy path (for UsoSvc /
# enforcement-deadline blocking, which is the H-B mechanism the audit
# trail confirmed as the leading-candidate caller of the Kernel API
# reboot). The Settings-UI registry alone does not block UsoSvc per
# Microsoft Learn `Policy CSP - Update`.
$policy_key = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"

try {
    # --- Settings-UI path (operator visibility) -----------------------
    if (-not (Test-Path $key)) {
        New-Item -Path $key -Force | Out-Null
    }
    Set-ItemProperty -Path $key -Name PauseUpdatesExpiryTime -Value $expiry -Type String
    Set-ItemProperty -Path $key -Name PauseFeatureUpdatesEndTime -Value $expiry -Type String
    Set-ItemProperty -Path $key -Name PauseQualityUpdatesEndTime -Value $expiry -Type String

    # --- Group-Policy path (enforcement; blocks UsoSvc) ---------------
    if (-not (Test-Path $policy_key)) {
        New-Item -Path $policy_key -Force | Out-Null
    }
    Set-ItemProperty -Path $policy_key -Name PauseFeatureUpdatesStartTime -Value $policy_start_iso -Type String
    Set-ItemProperty -Path $policy_key -Name PauseFeatureUpdatesEndTime   -Value $expiry          -Type String
    Set-ItemProperty -Path $policy_key -Name PauseQualityUpdatesStartTime -Value $policy_start_iso -Type String
    Set-ItemProperty -Path $policy_key -Name PauseQualityUpdatesEndTime   -Value $expiry          -Type String

    Write-Host "Windows Update paused (UTC) until $expiry (in $Hours hours from now)." -ForegroundColor Green
    Write-Host "  Settings UI key:   $key" -ForegroundColor Cyan
    Write-Host "  Group Policy key:  $policy_key" -ForegroundColor Cyan
    Write-Host "Verify with: Get-ItemProperty '$key' -Name PauseUpdatesExpiryTime" -ForegroundColor Cyan
    Write-Host "             Get-ItemProperty '$policy_key' -Name PauseFeatureUpdatesEndTime" -ForegroundColor Cyan
    Write-Host "To resume early: powershell.exe -ExecutionPolicy Bypass -File scripts\preflight\pause_windows_update.ps1 -Resume" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "ERROR setting pause: $_" -ForegroundColor Red
    exit 1
}
