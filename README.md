# 🥋 Sumo News Emailer

An AI-powered Python application that scrapes news from multiple sumo wrestling sources and converts them into bite-sized, tweet-like email summaries.

## Features

- 📰 **Multi-Source Scraping**: Automatically fetches news from multiple sumo sources:
  - Japan Sumo Association (sumo.or.jp)  
  - Japan Times Sumo Section
  - International Federation of Sumo (IFS)
- 🤖 **AI Processing**: Uses OpenAI to create engaging, tweet-like summaries (under 280 characters)
- ✉️ **Email Digest**: Sends formatted HTML and text emails with news summaries
- 🎯 **Smart Filtering**: Filters relevant news, removes duplicates, and shows source attribution
- 🛡️ **Rate Limiting**: Respectful scraping with built-in delays between sources
- 🔄 **Fallback Support**: Works with or without OpenAI API key (uses basic summaries as fallback)
- 📊 **SQLite Database**: Tracks all scraped articles, prevents duplicates, maintains processing history

## Setup

1. **Clone and install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Required environment variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `EMAIL_HOST`: SMTP server (e.g., smtp.gmail.com)
   - `EMAIL_PORT`: SMTP port (e.g., 587)
   - `EMAIL_USER`: Your email address
   - `EMAIL_PASS`: Your email password/app password
   - `EMAIL_TO`: Recipient email address

## Usage

**Run the main application**:
```bash
python src/main.py
```

**Test all components**:
```bash
python src/main.py --test
```

**Get help**:
```bash
python src/main.py --help
```

## Testing

**Quick scraping test (no setup required)**:
```bash
python test_scraping.py
```

**Test all components**:
```bash
python src/main.py --test
```

## Database Management

**View database statistics**:
```bash
python manage_db.py stats
```

**View recent articles**:
```bash
python manage_db.py recent
```

**View unprocessed articles**:
```bash
python manage_db.py unprocessed
```

**Clean up old articles** (removes articles older than 30 days):
```bash
python manage_db.py cleanup
```

## How It Works

1. **Multi-Source Scraping**: Fetches news from multiple sumo wrestling websites
2. **Database Storage**: Saves all articles to SQLite database with duplicate prevention
3. **Content Analysis**: Extracts relevant sumo news using keyword filtering and deduplication
4. **Source Attribution**: Labels each news item with its source for transparency
5. **AI Processing**: Creates concise, engaging summaries using OpenAI (or basic summaries as fallback)
6. **Email Generation**: Formats news into an attractive HTML/text email digest
7. **Processing Tracking**: Marks articles as processed to avoid re-sending
8. **Delivery**: Sends the digest to your specified email address

## Email Configuration

### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an "App Password" for this application
3. Use your Gmail address as `EMAIL_USER` and the app password as `EMAIL_PASS`

### Other Email Providers
- **Outlook**: Use `smtp-mail.outlook.com`, port 587
- **Yahoo**: Use `smtp.mail.yahoo.com`, port 587
- **Custom SMTP**: Use your provider's SMTP settings

## Sample Output

The application generates emails with:
- **Subject**: AI-generated engaging subject line
- **Introduction**: Brief intro paragraph
- **News Items**: Tweet-like summaries with links to full articles
- **Timestamps**: When articles were published and processed

## Automation

You can schedule this application to run daily using:

**Windows Task Scheduler**:
```cmd
schtasks /create /tn "SumoNews" /tr "python C:\path\to\src\main.py" /sc daily /st 09:00
```

**Linux/Mac Cron**:
```bash
# Add to crontab (runs daily at 9 AM)
0 9 * * * cd /path/to/sumo_updates && python src/main.py
```

## Troubleshooting

- **No news found**: The scraper looks for specific keywords. Check if the website structure changed.
- **Email errors**: Verify SMTP settings and app passwords
- **AI errors**: Confirm your OpenAI API key is valid and has credits
- **Rate limiting**: The app includes delays between requests to be respectful

## Dependencies

- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing and manipulation
- `openai`: AI text processing
- `python-dotenv`: Environment variable management
- `smtplib` & `email`: Built-in email sending functionality