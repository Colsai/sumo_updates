# Complete Setup Guide

This guide walks you through installing and configuring the Sumo News Emailer application from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Email Provider Setup](#email-provider-setup)
5. [OpenAI API Setup](#openai-api-setup)
6. [First Run & Testing](#first-run--testing)
7. [Automation Setup](#automation-setup)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Python 3.8 or higher** (Check with `python --version`)
- **Internet connection** for news scraping
- **Email account** with SMTP access
- **OpenAI API key** (optional but recommended)

### For Windows Users
- Git for Windows (optional, for cloning repository)
- PowerShell (for automation scripts)

### For Linux/Mac Users  
- pip package manager
- cron (for automation)

## Installation

### Method 1: Clone from GitHub (Recommended)

```bash
git clone https://github.com/Colsai/sumo_updates.git
cd sumo_updates
```

### Method 2: Download ZIP
1. Download the ZIP file from GitHub
2. Extract to your desired location
3. Navigate to the extracted folder

### Install Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt
```

**Dependencies installed:**
- `requests` - Web scraping
- `beautifulsoup4` - HTML parsing
- `openai` - AI text processing
- `python-dotenv` - Environment variables

## Configuration

### 1. Create Environment File

```bash
# Copy the example configuration
cp config/.env.example .env
```

### 2. Edit Configuration

Open `.env` in your text editor and fill in your credentials:

```env
# OpenAI Configuration (Optional but recommended)
OPENAI_API_KEY=sk-your-api-key-here

# Email SMTP Configuration (Required)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password-here
EMAIL_TO=recipient@example.com
```

## Email Provider Setup

### Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Turn on 2-Step Verification

2. **Generate App Password**
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Copy the 16-character password (no spaces)

3. **Configure .env**
   ```env
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=yourgmail@gmail.com
   EMAIL_PASS=abcd efgh ijkl mnop  # Your app password
   EMAIL_TO=recipient@example.com
   ```

### Outlook/Hotmail Setup

```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USER=your-email@outlook.com
EMAIL_PASS=your-password-here
EMAIL_TO=recipient@example.com
```

### Yahoo Mail Setup

```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USER=your-email@yahoo.com
EMAIL_PASS=your-app-password-here
EMAIL_TO=recipient@example.com
```

### Other Providers

Contact your email provider for SMTP settings. Most use:
- **Port**: 587 (STARTTLS) or 465 (SSL)
- **Security**: TLS/SSL enabled

## OpenAI API Setup

### 1. Get API Key

1. Visit [OpenAI Platform](https://platform.openai.com)
2. Create an account or log in
3. Go to [API Keys](https://platform.openai.com/account/api-keys)
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

### 2. Add Credits

1. Go to [Billing](https://platform.openai.com/account/billing)
2. Add payment method
3. Purchase credits ($5-10 is plenty for months of use)

### 3. Configure

Add your API key to `.env`:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Without OpenAI (Free Option)

The application works without OpenAI but generates basic summaries instead of AI-powered ones. Simply leave `OPENAI_API_KEY` empty or remove the line.

## First Run & Testing

### 1. Test Components

```bash
python main.py --test
```

**Expected Output:**
```
Testing Components
    
Testing application components...

Testing database...
Database: OK (total: 0 articles)

Testing email connection...
Email: OK

Testing news scraper...
Scraper: OK (found 10 items)

Testing AI processor...
AI: OK (Check out the results from the Test Sumo Tournament...)
```

### 2. Fix Any Issues

**Database Issues:**
- Check file permissions in `data/` folder
- Ensure SQLite is working: `python -c "import sqlite3; print('OK')"`

**Email Issues:**
- Verify SMTP settings
- Check app password (not regular password)
- Try telnet test: `telnet smtp.gmail.com 587`

**Scraper Issues:**
- Check internet connection
- Websites may be temporarily down
- Rate limiting (wait and try again)

**AI Issues:**
- Verify API key is correct
- Check OpenAI account has credits
- Test with: `python -c "import openai; print('OK')"`

### 3. First Full Run

```bash
python main.py
```

This will:
1. Scrape news from multiple sources
2. Process articles with AI
3. Generate email digest
4. Send to your configured email address

## Automation Setup

### Windows Task Scheduler

#### Option 1: PowerShell Script (Easy)

```powershell
# Run as Administrator
cd "C:\path\to\sumo_updates"
.\scripts\setup_task_scheduler.ps1
```

#### Option 2: Manual Setup

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task:
   - **Name**: SumoNewsWeeklyDigest
   - **Trigger**: Weekly, Sunday, 8:00 AM
   - **Action**: Start a program
   - **Program**: `C:\path\to\sumo_updates\scripts\run_sumo_news.bat`

### Linux/Mac Cron

```bash
# Edit crontab
crontab -e

# Add line for Sunday 8 AM
0 8 * * 0 cd /path/to/sumo_updates && python main.py

# Or use the batch script approach
0 8 * * 0 /path/to/sumo_updates/scripts/run_sumo_news.sh
```

### Docker (Advanced)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### "Permission denied" on database
```bash
# Fix file permissions (Linux/Mac)
chmod 755 data/
chmod 644 data/sumo_news.db

# Windows: Right-click data folder → Properties → Security
```

#### Email authentication failed
- Use app password, not account password
- Enable "Less secure app access" for some providers
- Check 2FA is enabled for Gmail

#### Unicode/encoding errors
- Ensure Python uses UTF-8: `python -c "import sys; print(sys.stdout.encoding)"`
- On Windows, set: `set PYTHONIOENCODING=utf-8`

#### Rate limiting / blocked requests
- Wait 10-15 minutes between runs
- Check if your IP is blocked
- Websites may have changed structure

### Debug Mode

Enable detailed logging:

```bash
# Set debug environment variable
export DEBUG=1
python main.py
```

### Getting Help

1. Check logs in `logs/` directory
2. Review error messages carefully
3. Test components individually: `python main.py --test`
4. Check GitHub issues for similar problems
5. Ensure all dependencies are up to date

### Log Files

Logs are automatically created in `logs/`:
```
logs/sumo_news_YYYY-MM-DD_HH-MM-SS.log
```

Check recent logs:
```bash
# View latest log
ls -lt logs/ | head -1

# View log content
cat logs/sumo_news_*.log | tail -50
```

## Advanced Configuration

### Custom Scheduling

Edit the batch/shell scripts to change timing:
- `scripts/run_sumo_news.bat` (Windows)
- `scripts/run_sumo_news.sh` (Linux/Mac)

### Database Management

```bash
# View database stats
python tests/manage_db.py stats

# Clean old articles
python tests/manage_db.py cleanup

# View recent articles
python tests/manage_db.py recent
```

### Email Customization

Edit email templates in `src/emailer.py`:
- HTML styling (line 91)
- Email subject generation (AI processor)
- Header image location

### Adding News Sources

Edit `src/scraper.py` to add new sources:
```python
self.sources = [
    {
        'name': 'New Source',
        'url': 'https://example.com',
        'parser': self._parse_new_source
    }
]
```

## Security Best Practices

1. **Never commit .env file** - Contains sensitive credentials
2. **Use app passwords** - Don't use main account passwords
3. **Rotate API keys** - Periodically update OpenAI keys
4. **Monitor usage** - Check OpenAI billing regularly
5. **Restrict file permissions** - Secure config and data directories

---

**Setup complete!** Your sumo news digest should now run automatically and send weekly emails with the latest sumo wrestling news.