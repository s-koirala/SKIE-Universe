# P1-PREFLIGHT-USOSVC-TASK-DISABLE (BLOCKING for next H050 launch)
#
# Manages the UsoSvc internal reboot tasks under
# `\Microsoft\Windows\UpdateOrchestrator\` for the duration of a long-running
# walk-forward run. Per the H050 production-run post-mortem
# (docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md §5.2):
#
# > The reboot path on this host is the internal UsoSvc Task Scheduler tree --
# > `\Microsoft\Windows\UpdateOrchestrator\Reboot_AC`, `Reboot_Battery`,
# > `Universal Orchestrator Start` -- which is NOT WUfB. The canonical
# > mitigation for the UsoSvc path is to enumerate and temporarily disable
# > the registered Reboot* tasks for the run window.
#
# This helper is the canonical implementation of that mitigation. It is the
# Layer-5 protection registered by `P1-ADR-0010-LAYER-AMENDMENT`.
#
# Implementation: uses the `Get-ScheduledTask` / `Disable-ScheduledTask` /
# `Enable-ScheduledTask` PowerShell cmdlets (Round-1 audit F-1-6 fix from
# the locale-sensitive `schtasks /Query /V /FO LIST` text-parsing
# implementation). Get-ScheduledTask returns a structured CimInstance with
# a `.State` property (Disabled / Ready / Running enum) — locale-invariant.
#
# Usage:
#   List the tasks:
#     pwsh -File manage_usosvc_reboot_tasks.ps1 -Action List
#
#   Disable for run window (saves prior state to JSON):
#     pwsh -File manage_usosvc_reboot_tasks.ps1 -Action Disable -StatePath disable_state.json
#
#   Re-enable from saved state on exit:
#     pwsh -File manage_usosvc_reboot_tasks.ps1 -Action Enable -StatePath disable_state.json
#
# Exit codes:
#   0 = success
#   1 = at least one task could not be modified (does NOT block; re-enable
#       still attempted on the rest)
#   2 = elevation required (Disable/Enable-ScheduledTask requires Admin
#       context for protected tasks under `\Microsoft\Windows\`)
#   3 = state file not found (Enable mode only)
#
# Operator-supplied -TaskPatterns: pass each pattern as a separate
# argument after `-TaskPatterns`. PowerShell will collect them into the
# [string[]] parameter via the `,` array literal:
#     -TaskPatterns 'Reboot_AC','Reboot_Battery'
#
# Reference:
# - docs/decisions/ADR-0010-multi-hour-run-process-protection.md Layer 5
# - docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md §5.2
# - Microsoft Docs Get-ScheduledTask:
#   https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/get-scheduledtask

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("List", "Disable", "Enable")]
    [string]$Action,

    # State JSON path. Required for Disable + Enable. List ignores.
    [string]$StatePath = "",

    # Task-name patterns to match under `\Microsoft\Windows\UpdateOrchestrator\`.
    # Default = canonical 3-task USOSvc reboot tasks per post-mortem §5.2.
    # Operators needing extras (e.g., "Schedule Reboot", "Schedule Wakeup")
    # should pass them via this parameter with a documented rationale.
    [string[]]$TaskPatterns = @(
        "Reboot_AC",
        "Reboot_Battery",
        "Universal Orchestrator Start"
    ),

    # Parent task-folder. Allows test fixtures to point at a synthetic folder.
    [string]$TaskFolder = "\Microsoft\Windows\UpdateOrchestrator\"
)

$ErrorActionPreference = "Stop"

function Get-TaskInfo {
    param([string]$TaskName, [string]$Folder)
    # Enumerate-then-filter pattern (locale-invariant; avoids catching
    # CIM-specific exception types whose names vary across PS versions).
    # `-ErrorAction SilentlyContinue` swallows the empty-folder error
    # without polluting the error stream; missing-task is then a simple
    # "no Where-Object match" rather than a thrown exception.
    try {
        $all = Get-ScheduledTask -TaskPath $Folder -ErrorAction SilentlyContinue
        $task = $all | Where-Object { $_.TaskName -eq $TaskName } | Select-Object -First 1
        if ($null -eq $task) {
            return @{
                task_path = ($Folder.TrimEnd("\") + "\" + $TaskName)
                task_name = $TaskName
                state     = "not_present"
                present   = $false
            }
        }
        return @{
            task_path = ($Folder.TrimEnd("\") + "\" + $TaskName)
            task_name = $TaskName
            state     = $task.State.ToString()
            present   = $true
        }
    } catch {
        return @{
            task_path = ($Folder.TrimEnd("\") + "\" + $TaskName)
            task_name = $TaskName
            state     = "query_error"
            present   = $false
            error     = "$_"
        }
    }
}

function Set-TaskState {
    # Action = "Disable" or "Enable" (case-sensitive PS verbs)
    param([string]$TaskName, [string]$Folder, [string]$Action)
    try {
        if ($Action -eq "Disable") {
            $null = Disable-ScheduledTask -TaskPath $Folder -TaskName $TaskName -ErrorAction Stop
        } elseif ($Action -eq "Enable") {
            $null = Enable-ScheduledTask -TaskPath $Folder -TaskName $TaskName -ErrorAction Stop
        } else {
            return @{ ok = $false; exitCode = -1; output = "unknown action: $Action" }
        }
        return @{ ok = $true; exitCode = 0; output = "" }
    } catch [System.UnauthorizedAccessException] {
        return @{ ok = $false; exitCode = 5; output = "access denied: $_" }
    } catch {
        $msg = "$_"
        $isAccess = ($msg -match "[Aa]ccess" -and $msg -match "[Dd]enied")
        return @{
            ok       = $false
            exitCode = if ($isAccess) { 5 } else { -1 }
            output   = $msg
        }
    }
}

function Write-StateFileAtomic {
    param([hashtable]$Payload, [string]$Path)
    # F-1-7 fix: same-volume check for atomic Move-Item.
    $tmp = "$Path.tmp"
    $tmp_root = [System.IO.Path]::GetPathRoot($tmp)
    $dst_root = [System.IO.Path]::GetPathRoot($Path)
    if ($tmp_root -ne $dst_root) {
        throw "StatePath '$Path' and tmp '$tmp' are on different volumes; Move-Item is not atomic across volumes."
    }
    $Payload | ConvertTo-Json -Depth 6 | Set-Content -Path $tmp -Encoding UTF8
    Move-Item -Path $tmp -Destination $Path -Force
}

# ============================================================================
# Action: List
# ============================================================================
if ($Action -eq "List") {
    $tasks = @()
    foreach ($pattern in $TaskPatterns) {
        $info = Get-TaskInfo -TaskName $pattern -Folder $TaskFolder
        $tasks += $info
    }
    @{
        action       = "List"
        task_folder  = $TaskFolder
        patterns     = $TaskPatterns
        tasks        = $tasks
        ts           = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    } | ConvertTo-Json -Depth 4
    exit 0
}

# ============================================================================
# Action: Disable (save state to StatePath)
# ============================================================================
if ($Action -eq "Disable") {
    if ([string]::IsNullOrEmpty($StatePath)) {
        Write-Error "StatePath is required for -Action Disable."
        exit 2
    }
    $disable_results = @()
    $any_failed = $false
    $needs_elevation = $false
    $original_state = @{}
    foreach ($pattern in $TaskPatterns) {
        $info = Get-TaskInfo -TaskName $pattern -Folder $TaskFolder
        $original_state[$pattern] = $info
        if (-not $info.present) {
            $disable_results += @{
                task_name = $pattern
                action    = "skip_not_present"
                ok        = $true
            }
            continue
        }
        $result = Set-TaskState -TaskName $pattern -Folder $TaskFolder -Action "Disable"
        if (-not $result.ok) {
            $any_failed = $true
            if ($result.exitCode -eq 5) {
                $needs_elevation = $true
            }
        }
        $disable_results += @{
            task_name      = $pattern
            action         = "disable"
            ok             = $result.ok
            exit_code      = $result.exitCode
            output         = $result.output
            previous_state = $info.state
        }
    }
    $payload = @{
        action            = "Disable"
        task_folder       = $TaskFolder
        patterns          = $TaskPatterns
        original_state    = $original_state
        disable_results   = $disable_results
        any_failed        = $any_failed
        needs_elevation   = $needs_elevation
        ts                = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    }
    Write-StateFileAtomic -Payload $payload -Path $StatePath
    # Echo to stdout for caller
    $payload | ConvertTo-Json -Depth 6
    if ($needs_elevation) { exit 2 }
    if ($any_failed)      { exit 1 }
    exit 0
}

# ============================================================================
# Action: Enable (restore from StatePath)
# ============================================================================
if ($Action -eq "Enable") {
    if ([string]::IsNullOrEmpty($StatePath)) {
        Write-Error "StatePath is required for -Action Enable."
        exit 2
    }
    if (-not (Test-Path $StatePath)) {
        Write-Error "StatePath '$StatePath' does not exist; cannot restore."
        exit 3
    }
    $state = Get-Content -Path $StatePath -Raw | ConvertFrom-Json
    $enable_results = @()
    $any_failed = $false
    $needs_elevation = $false
    foreach ($pattern in $state.patterns) {
        $orig = $state.original_state.$pattern
        if (-not $orig.present) {
            $enable_results += @{
                task_name = $pattern
                action    = "skip_not_present_at_disable"
                ok        = $true
            }
            continue
        }
        # Round-trip semantics: restore to ORIGINAL state. If a task was
        # originally Disabled (a prior operator action OR an OS state we
        # should not toggle), leave it Disabled.
        $target_action = if ($orig.state -ieq "Disabled") { "Disable" } else { "Enable" }
        $result = Set-TaskState -TaskName $pattern -Folder $state.task_folder -Action $target_action
        if (-not $result.ok) {
            $any_failed = $true
            if ($result.exitCode -eq 5) {
                $needs_elevation = $true
            }
        }
        $enable_results += @{
            task_name      = $pattern
            action         = $target_action.ToLower()
            ok             = $result.ok
            exit_code      = $result.exitCode
            output         = $result.output
            restored_state = $orig.state
        }
    }
    @{
        action          = "Enable"
        state_path      = $StatePath
        enable_results  = $enable_results
        any_failed      = $any_failed
        needs_elevation = $needs_elevation
        ts              = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    } | ConvertTo-Json -Depth 4
    if ($needs_elevation) { exit 2 }
    if ($any_failed)      { exit 1 }
    exit 0
}
