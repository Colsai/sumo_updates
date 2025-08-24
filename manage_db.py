#!/usr/bin/env python3
"""
Database management script for Sumo News Emailer
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import NewsDatabase
from scraper import SumoNewsScraper

def show_stats():
    """Show database statistics"""
    scraper = SumoNewsScraper()
    stats = scraper.get_database_stats()
    
    print("Database Statistics:")
    print("=" * 30)
    print(f"Total articles: {stats['total_articles']}")
    print(f"Processed: {stats['processed_articles']}")
    print(f"Unprocessed: {stats['unprocessed_articles']}")
    print(f"Last 24 hours: {stats['articles_last_24h']}")
    print("\nBy source:")
    for source, count in stats['articles_by_source'].items():
        print(f"  {source}: {count}")

def show_recent():
    """Show recent articles"""
    db = NewsDatabase()
    articles = db.get_recent_articles(days=7, limit=20)
    
    print("Recent Articles (Last 7 days):")
    print("=" * 50)
    
    for article in articles:
        status = "DONE" if article['processed'] else "TODO"
        try:
            # Handle Unicode encoding issues
            title = article['title'][:60].encode('ascii', errors='replace').decode('ascii')
            print(f"{status} [{article['source']}] {title}...")
            print(f"   {article['url']}")
            print(f"   Scraped: {article['scraped_at'][:19]}")
            print()
        except Exception as e:
            print(f"{status} [{article['source']}] <Title encoding error>")
            print(f"   {article['url']}")
            print()

def show_unprocessed():
    """Show unprocessed articles"""
    db = NewsDatabase()
    articles = db.get_unprocessed_articles(limit=50)
    
    print(f"Unprocessed Articles ({len(articles)}):")
    print("=" * 40)
    
    for article in articles:
        print(f"[{article['source']}] {article['title']}")
        print(f"   {article['url']}")
        print(f"   Scraped: {article['scraped_at'][:19]}")
        print()

def cleanup():
    """Clean up old articles"""
    print("Cleaning up articles older than 30 days...")
    db = NewsDatabase()
    deleted = db.cleanup_old_articles(days=30)
    print(f"Deleted {deleted} old articles.")

def reset_processed():
    """Reset all articles to unprocessed (for testing)"""
    import sqlite3
    
    confirm = input("Are you sure you want to mark all articles as unprocessed? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    with sqlite3.connect('sumo_news.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE news_articles SET processed = FALSE, processed_at = NULL, summary = NULL')
        updated = cursor.rowcount
        conn.commit()
    
    print(f"Reset {updated} articles to unprocessed.")

def show_help():
    print("""
Database Management Commands:

  python manage_db.py stats      - Show database statistics
  python manage_db.py recent     - Show recent articles (last 7 days)
  python manage_db.py unprocessed - Show unprocessed articles
  python manage_db.py cleanup    - Remove articles older than 30 days
  python manage_db.py reset      - Mark all articles as unprocessed (testing)
  python manage_db.py help       - Show this help
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        show_stats()
    elif command == "recent":
        show_recent()
    elif command == "unprocessed":
        show_unprocessed()
    elif command == "cleanup":
        cleanup()
    elif command == "reset":
        reset_processed()
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)