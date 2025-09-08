# Sumo News Digest

🤼‍♂️ AI-powered Python application that scrapes sumo wrestling news and sends weekly email digests with smart summaries and educational content.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure**:
   ```bash
   cp .env.example .env
   # Edit .env with your email and OpenAI credentials
   ```

3. **Run**:
   ```bash
   python main.py
   ```

## ✨ What It Does

### 🔍 **Smart Content Gathering**
- Scrapes news from Japan Sumo Association, Japan Times, and IFS Sumo
- **Vector database** with semantic duplicate detection
- **AI-powered tagging** system for content organization
- **Email clash prevention** to avoid repeating content

### 🤖 **AI-Enhanced Processing**  
- Creates engaging summaries using OpenAI GPT
- **Bite-sized Sumo** educational tips in each email
- Smart content filtering and similarity analysis
- Automatic entity and topic extraction

### 📧 **Professional Email Delivery**
- Beautiful HTML email templates with embedded banner
- Plain text versions for compatibility  
- Automated archiving for record keeping
- Comprehensive tracking and statistics

### 🛡️ **Robust & Reliable**
- SQLite vector database for efficient storage
- Automatic duplicate prevention
- Error handling and recovery
- Can be automated via Task Scheduler

## 🚀 Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Run the main application |
| `python main.py --dry-run` | Generate email without sending (for testing) |
| `python main.py --test` | Test all components |
| `python main.py --help` | Show help information |
| `python tests/test_pipeline.py` | Test complete pipeline with output files |

## Documentation

- **[Complete Setup Guide](docs/SETUP_GUIDE.md)** - Detailed installation and configuration
- **[User Manual](docs/USER_MANUAL.md)** - In-depth usage instructions  
- **[Task Scheduler Setup](docs/TASK_SCHEDULER_SETUP.md)** - Automated weekly runs
- **[Example Email](docs/EXAMPLE_EMAIL.md)** - Sample output format

## 📁 Project Structure

```
sumo_updates/
├── main.py                # Main entry point
├── .env.example          # Environment configuration template
├── requirements.txt      # Python dependencies
├── src/                  # Core application code  
│   ├── main.py          # Main application logic
│   ├── scraper.py       # Web scraping functionality
│   ├── ai_processor.py  # OpenAI integration & processing
│   ├── emailer.py       # Email generation & sending
│   ├── database.py      # Vector database management
│   ├── similarity_analyzer.py  # Content similarity analysis
│   ├── email_clash_checker.py  # Duplicate email prevention
│   ├── tag_manager.py   # Article tagging system
│   └── sumo_tip_manager.py     # Educational content management
├── data/                # Database storage (auto-created)
├── scripts/             # Automation scripts
├── tests/               # Test utilities & validation
├── docs/                # Documentation
├── assets/              # Images and static files
│   └── images/         # Email banner and graphics
├── logs/                # Application logs (auto-created)
└── archives/            # Email archives (auto-created)
```

## 🔧 Key Features

- **Vector Database**: Uses sqlite-vec for semantic similarity search
- **AI Processing**: GPT-powered content summarization and analysis  
- **Smart Tagging**: Automatic content categorization and organization
- **Educational Content**: Bite-sized Sumo facts to engage readers
- **Email Management**: Professional HTML/text templates with tracking
- **Clash Prevention**: Prevents duplicate content across email sends
- **Testing Suite**: Comprehensive testing and validation tools

## License

This project is open source. Feel free to modify and distribute.