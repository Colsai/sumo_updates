# Sumo News Weekly Task Scheduler Setup

This guide helps you set up the Sumo News Digest to run automatically every week using Windows Task Scheduler.

## Quick Setup (Recommended)

### Option 1: PowerShell Script (Easiest)

1. **Right-click** on PowerShell and select **"Run as Administrator"**
2. Navigate to the project directory:
   ```powershell
   cd "C:\Users\schir\sumo_updates"
   ```
3. Run the setup script:
   ```powershell
   .\setup_task_scheduler.ps1
   ```
4. The task will be created to run every **Sunday at 8:00 AM**

### Option 2: Manual Task Scheduler Setup

1. Press **Win + R**, type `taskschd.msc`, and press Enter
2. In Task Scheduler, click **"Create Basic Task"** in the right panel
3. Fill out the wizard:
   - **Name**: `SumoNewsWeeklyDigest`
   - **Description**: `Weekly Sumo Wrestling News Digest`
   - **Trigger**: Weekly
   - **Day**: Sunday
   - **Time**: 8:00 AM (or your preferred time)
   - **Action**: Start a program
   - **Program**: Browse to `C:\Users\schir\sumo_updates\run_sumo_news.bat`
   - **Start in**: `C:\Users\schir\sumo_updates`

## Configuration

### Changing Schedule
To modify when the task runs:
1. Open Task Scheduler (`taskschd.msc`)
2. Find **SumoNewsWeeklyDigest** in the task list
3. Right-click → **Properties**
4. Go to **Triggers** tab → Edit
5. Modify the schedule as needed

### Log Files
- Logs are saved in `C:\Users\schir\sumo_updates\logs\`
- Format: `sumo_news_YYYY-MM-DD_HH-MM-SS.log`
- Old logs (30+ days) are automatically cleaned up

## Testing

### Test the Batch Script
```cmd
cd "C:\Users\schir\sumo_updates"
run_sumo_news.bat
```

### Test the Scheduled Task
```powershell
Start-ScheduledTask -TaskName "SumoNewsWeeklyDigest"
```

### Check Task Status
```powershell
Get-ScheduledTask -TaskName "SumoNewsWeeklyDigest"
```

## Troubleshooting

### Task Won't Run
1. Check that Python is in your system PATH
2. Verify your `.env` file has valid email credentials
3. Check the log files for error messages
4. Ensure the task is set to run whether user is logged on or not

### Email Issues
1. Test email configuration: `cd src && python main.py --test`
2. For Gmail: Use App Password instead of regular password
3. Check firewall/antivirus blocking SMTP connections

### Python Path Issues
If Python isn't found, edit `run_sumo_news.bat` and change:
```batch
python main.py
```
to:
```batch
"C:\Path\To\Your\Python.exe" main.py
```

## Important Notes

- **Email credentials** must be configured in `.env` file
- **Internet connection** required for news scraping
- Task runs with **current user permissions**
- Logs help diagnose any issues

## Maintenance

### View Recent Logs
```cmd
cd "C:\Users\schir\sumo_updates\logs"
dir /od
type sumo_news_*.log
```

### Update Schedule
Modify the PowerShell script and re-run, or use Task Scheduler GUI.

### Remove Task
```powershell
Unregister-ScheduledTask -TaskName "SumoNewsWeeklyDigest" -Confirm:$false
```

---

✅ **Setup Complete!** Your sumo news digest will now run automatically every Sunday at 8:00 AM.