# User Manual

Complete guide to using the Sumo News Emailer application.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Command Line Options](#command-line-options)
3. [Database Management](#database-management)
4. [Email Archives](#email-archives)
5. [Testing & Debugging](#testing--debugging)
6. [Customization](#customization)
7. [Monitoring & Logs](#monitoring--logs)
8. [FAQ](#faq)

## Basic Usage

### Running the Application

**Main command** (run from project root):
```bash
python main.py
```

**What happens when you run it:**

1. **Scraping Phase**
   - Connects to Japan Sumo Association website
   - Connects to Japan Times Sumo section  
   - Connects to International Federation of Sumo
   - Extracts relevant news articles
   - Filters out duplicates and irrelevant content

2. **Database Phase**
   - Saves new articles to SQLite database
   - Checks for duplicates using URL hashing
   - Updates article metadata and timestamps

3. **AI Processing Phase** (if OpenAI key provided)
   - Sends article content to OpenAI
   - Generates tweet-like summaries (under 280 chars)
   - Creates engaging email subject and intro

4. **Email Phase**
   - Generates HTML and text versions of email
   - Embeds header image
   - Sends digest to configured recipient
   - Archives email copy to `archives/` folder

5. **Cleanup Phase**
   - Marks processed articles in database
   - Updates statistics
   - Logs completion status

### Expected Output

```
    Sumo News Emailer
         ___
        ( o.o )
         \_/
    
Starting Sumo News Digest Generation...
==================================================
Scraping news from multiple sources...
  Fetching from Japan Sumo Association...
  Fetching from Japan Times Sumo...
  Fetching from IFS Sumo...
Found 15 total news items from all sources
Saved 3 new articles to database
Getting unprocessed articles from database...
Found 8 unprocessed news items:
  1. [Japan Sumo Association] Onosato Promoted As The 75th Yokozuna...
  2. [Japan Times] Tournament Results Show Strong Performance...
  ...

Fetching article content...

Processing with AI...
AI summaries generated:
  1. Onosato makes history as newest yokozuna! The rising star...
  2. Latest tournament shows incredible competitive matches...
  ...

Creating email digest...
Email subject: Weekly Sumo Digest: New Yokozuna & Tournament Highlights!
Email intro: This week brings exciting developments from the sumo world...

Sending email...
Email sent successfully!
Message ID: <unique-message-id>

Articles marked as processed in database.

Database Stats:
  Total articles: 125
  Processed: 95
  Unprocessed: 30
  Last 24h: 15

    Digest Complete! \o/
    
    Sumo News Digest completed successfully!
```

## Command Line Options

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `python main.py` | Run full application | Creates and sends email digest |
| `python main.py --test` | Test all components | Verifies database, email, scraper, AI |
| `python main.py --help` | Show help information | Displays usage instructions |

### Test Mode Details

**Test mode** (`--test`) checks each component:

```
Testing Components
         (^_^)
    
Testing application components...

Testing database...
Database: OK (total: 125 articles)

Testing email connection...
Email: OK

Testing news scraper...
  Fetching from Japan Sumo Association...
  Fetching from Japan Times Sumo...
  Fetching from IFS Sumo...
Found 29 total news items from all sources
Scraper: OK (found 10 items)

Testing AI processor...
AI: OK (Sumo tournament results show strong competition...)
```

**What gets tested:**
- Database connectivity and stats
- SMTP email connection (no email sent)
- News scraping from all sources
- AI processing with sample article

## Database Management

The application uses SQLite database stored at `data/sumo_news.db`.

### Database Utilities

Located in `tests/manage_db.py`:

```bash
# View database statistics
python tests/manage_db.py stats

# View recent articles (last 10)
python tests/manage_db.py recent

# View unprocessed articles ready for email
python tests/manage_db.py unprocessed

# Clean up old articles (removes 30+ day old processed articles)
python tests/manage_db.py cleanup

# Reset processing status (mark all as unprocessed)
python tests/manage_db.py reset
```

### Database Schema

**news_articles table:**
- `id` - Primary key
- `title` - Article headline
- `url` - Source URL
- `content` - Scraped article text
- `source` - Website source name
- `article_date` - Publication date
- `scraped_at` - When we found it
- `url_hash` - For duplicate detection
- `processed` - Whether included in email (0/1)
- `summary` - AI-generated summary
- `processed_at` - When emailed

### Manual Database Access

```bash
# Direct SQLite access
python -c "
import sqlite3
conn = sqlite3.connect('data/sumo_news.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM news_articles')
print(f'Total articles: {cursor.fetchone()[0]}')
conn.close()
"
```

## Email Archives

Every sent email is automatically archived to `archives/` folder.

### Archive Files

For each email sent:
- `email_YYYYMMDD_HHMMSS.json` - Complete email data
- `email_YYYYMMDD_HHMMSS.html` - HTML version for viewing

### Viewing Archives

```bash
# List all archived emails
ls archives/

# View archive utility
python tests/view_archives.py

# View specific archive
python tests/view_archives.py archives/email_20250901_213937.json
```

### Archive Contents

The JSON archive contains:
```json
{
  "timestamp": "2025-09-01T21:39:37.123456",
  "subject": "Weekly Sumo Digest: New Yokozuna Promotion!",
  "intro": "This week brings exciting developments...",
  "recipient": "your-email@example.com",
  "article_count": 8,
  "articles": [
    {
      "title": "Onosato Promoted As The 75th Yokozuna",
      "url": "https://www.sumo.or.jp/...",
      "summary": "Historic promotion as Onosato becomes...",
      "source": "Japan Sumo Association",
      "date": "2025-08-24"
    }
  ],
  "html_content": "<!DOCTYPE html>...",
  "text_content": "SUMO WRESTLING NEWS DIGEST..."
}
```

## Testing & Debugging

### Component Testing

**Individual component tests:**

```bash
# Test just the scraper (no database saves)
python -c "
from src.scraper import SumoNewsScraper
scraper = SumoNewsScraper()
news = scraper.scrape_news(save_to_db=False)
print(f'Found {len(news)} items')
"

# Test email connection only
python -c "
import os
from dotenv import load_dotenv
from src.emailer import EmailSender
load_dotenv()
config = {
    'host': os.getenv('EMAIL_HOST'),
    'port': os.getenv('EMAIL_PORT'),
    'user': os.getenv('EMAIL_USER'),
    'pass': os.getenv('EMAIL_PASS')
}
emailer = EmailSender(config)
print('Connection OK' if emailer.test_connection() else 'Connection Failed')
"
```

### Debug Mode

Enable verbose logging:

```bash
# Windows
set DEBUG=1
python main.py

# Linux/Mac
DEBUG=1 python main.py
```

### Common Issues & Solutions

**No news items found:**
- Check internet connection
- Websites may be down temporarily
- Site structure may have changed
- Try running test mode: `python main.py --test`

**Email authentication failed:**
- Verify app password (not account password)
- Check 2FA is enabled
- Test with: `telnet smtp.gmail.com 587`

**AI processing errors:**
- Check OpenAI API key validity
- Verify account has credits
- API may be temporarily down

**Unicode/encoding errors:**
- Common on Windows
- Set environment: `set PYTHONIOENCODING=utf-8`

## Customization

### Email Styling

Edit `src/emailer.py` around line 91 to customize HTML:

```python
# Change colors, fonts, layout
html_content = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{email_meta['subject']}</title>
</head>
<body style="font-family: Arial; color: #333; background: #f5f5f5;">
  <!-- Your custom styling -->
</body>
</html>'''
```

### Email Subject & Intro

Modify AI prompts in `src/ai_processor.py`:

```python
def create_email_digest(self, summaries):
    prompt = f"""
    Create an engaging email subject and intro for these sumo news items.
    Make it exciting and informative!
    
    Articles: {summaries}
    
    Return JSON with 'subject' and 'intro' fields.
    """
```

### Adding News Sources

Add new sources in `src/scraper.py`:

```python
self.sources = [
    # Existing sources...
    {
        'name': 'Your New Source',
        'url': 'https://example.com/sumo-news',
        'parser': self._parse_your_new_source
    }
]

def _parse_your_new_source(self, url):
    # Your parsing logic
    return news_items
```

### Scheduling Changes

**Change frequency:**
- Edit `scripts/setup_task_scheduler.ps1`
- Modify trigger from Weekly to Daily/Monthly
- Update time from 8:00 AM to preferred time

**Multiple schedules:**
- Create multiple tasks with different names
- Different recipients for different schedules
- Separate databases for different topics

## Monitoring & Logs

### Log Files

**Location:** `logs/sumo_news_YYYY-MM-DD_HH-MM-SS.log`

**View recent logs:**
```bash
# Latest log
ls -t logs/ | head -1

# View log content  
tail -50 logs/sumo_news_*.log

# Search for errors
grep -i error logs/sumo_news_*.log
```

### Log Rotation

Logs auto-cleanup after 30 days. Modify in `scripts/run_sumo_news.bat`:

```batch
REM Keep only last 10 log files
forfiles /p logs /m sumo_news_*.log /c "cmd /c del @path" /d -30
```

### Monitoring Checklist

**Weekly checks:**
- Email digests being received
- No error messages in logs  
- Database growing with new articles
- Archive files being created
- OpenAI costs within budget

**Monthly checks:**
- Clean old logs and archives
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Check for website structure changes
- Rotate API keys for security

### Performance Monitoring

**Database growth:**
```bash
python -c "
import os
size = os.path.getsize('data/sumo_news.db')
print(f'Database size: {size//1024//1024}MB')
"
```

**OpenAI usage:**
- Check [OpenAI Usage Dashboard](https://platform.openai.com/account/usage)
- Monitor costs per month
- Typical usage: $0.50-2.00 per month

## FAQ

### General Questions

**Q: How often should I run this?**  
A: Weekly is recommended. Daily may result in duplicate content, monthly may miss time-sensitive news.

**Q: Can I run this without OpenAI?**  
A: Yes! Remove or leave empty the `OPENAI_API_KEY`. You'll get basic summaries instead of AI-generated ones.

**Q: What if no news is found?**  
A: The application will log this and exit gracefully. No email is sent. This is normal if sources have no new content.

**Q: Can I send to multiple recipients?**  
A: Currently supports one recipient. For multiple, run the application multiple times with different `EMAIL_TO` settings.

### Technical Questions

**Q: Can I run this on a server?**  
A: Yes! Use cron for scheduling. Ensure all dependencies are installed and paths are absolute.

**Q: How much does OpenAI cost?**  
A: Typically $0.50-2.00 per month for weekly digests. Depends on article length and frequency.

**Q: What if a website blocks the scraper?**  
A: The application includes rate limiting and respectful headers. If blocked, wait and try again later.

**Q: Can I change the email template?**  
A: Yes! Edit `src/emailer.py` methods `_generate_html_email()` and `_generate_text_email()`.

### Troubleshooting

**Q: "Module not found" errors**  
A: Run `pip install -r requirements.txt` to ensure all dependencies are installed.

**Q: Email not sending**  
A: Test connection with `python main.py --test`. Check SMTP settings and app passwords.

**Q: Unicode errors on Windows**  
A: Set `PYTHONIOENCODING=utf-8` environment variable before running.

**Q: Task Scheduler not working**  
A: Ensure task runs "whether user is logged on or not" and uses full paths to Python and script.

---

**Happy sumo news reading!** This manual covers all aspects of using the application. For technical setup details, see the [Setup Guide](SETUP_GUIDE.md).