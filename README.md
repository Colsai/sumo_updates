# Sumo News Emailer

AI-powered Python application that scrapes sumo wrestling news and sends weekly email digests with smart summaries.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure**:
   ```bash
   cp config/.env.example .env
   # Edit .env with your email and OpenAI credentials
   ```

3. **Run**:
   ```bash
   python main.py
   ```

## What It Does

- Scrapes news from Japan Sumo Association, Japan Times, and IFS Sumo
- Creates AI-powered summaries using OpenAI
- Sends formatted HTML email digests
- Can be automated to run weekly via Task Scheduler
- Tracks articles in SQLite database to prevent duplicates

## Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Run the main application |
| `python main.py --test` | Test all components |
| `python main.py --help` | Show help information |

## Documentation

- **[Complete Setup Guide](docs/SETUP_GUIDE.md)** - Detailed installation and configuration
- **[User Manual](docs/USER_MANUAL.md)** - In-depth usage instructions  
- **[Task Scheduler Setup](docs/TASK_SCHEDULER_SETUP.md)** - Automated weekly runs
- **[Example Email](docs/EXAMPLE_EMAIL.md)** - Sample output format

## Project Structure

```
sumo_updates/
├── main.py                # Main entry point
├── src/                   # Core application code  
├── config/               # Configuration files
├── data/                 # Database storage
├── scripts/              # Automation scripts
├── tests/                # Test utilities
├── docs/                 # Documentation
├── assets/               # Images and static files
├── logs/                 # Application logs (auto-created)
└── archives/             # Email archives (auto-created)
```

## License

This project is open source. Feel free to modify and distribute.