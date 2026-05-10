# TrailerPark Windows Task Scheduler setup
# Run as Administrator: powershell -ExecutionPolicy Bypass -File scripts\install-task-scheduler.ps1

$taskName = "TrailerPark"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
$startScript = Join-Path $scriptDir "start.bat"

# Remove existing task if it exists
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing scheduled task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the task action
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$startScript`"" `
    -WorkingDirectory $projectDir

# Trigger: at user logon
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -Hidden

# Register the task (runs as current user, no admin needed)
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "TrailerPark - Truck listing email aggregator" `
    -RunLevel Limited

Write-Host ""
Write-Host "Task '$taskName' registered successfully."
Write-Host "TrailerPark will start automatically when you log in."
Write-Host ""
Write-Host "To remove: Unregister-ScheduledTask -TaskName '$taskName'"
