# PowerShell script to create a weekly scheduled task for Sumo News Digest
# Run this script as Administrator

$TaskName = "SumoNewsWeeklyDigest"
$ScriptPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BatchFile = Join-Path $ScriptPath "scripts\run_sumo_news.bat"

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "This script requires Administrator privileges. Please run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "Setting up weekly scheduled task: $TaskName" -ForegroundColor Green

try {
    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Create the action (what to run)
    $Action = New-ScheduledTaskAction -Execute $BatchFile -WorkingDirectory $ScriptPath

    # Create the trigger (when to run) - Every Sunday at 8:00 AM
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "08:00"

    # Create task settings
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

    # Create the principal (run as current user)
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Weekly Sumo Wrestling News Digest - Scrapes news and sends email digest"

    Write-Host "Task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "The task will run every Sunday at 8:00 AM" -ForegroundColor Cyan
    Write-Host "Batch file location: $BatchFile" -ForegroundColor Cyan

    # Show the created task
    Get-ScheduledTask -TaskName $TaskName | Format-Table -AutoSize

} catch {
    Write-Host "Error creating scheduled task: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nTask setup complete! You can manage it through:" -ForegroundColor Green
Write-Host "1. Task Scheduler GUI (taskschd.msc)" -ForegroundColor White
Write-Host "2. PowerShell: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "3. To test now: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White