import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import os


class NewsDatabase:
    def __init__(self, db_path: str = 'sumo_news.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create news_articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    content TEXT,
                    source TEXT NOT NULL,
                    article_date TEXT,
                    scraped_at TEXT NOT NULL,
                    url_hash TEXT UNIQUE NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    summary TEXT,
                    processed_at TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_hash ON news_articles(url_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON news_articles(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraped_at ON news_articles(scraped_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed ON news_articles(processed)')
            
            conn.commit()

    def _generate_url_hash(self, url: str) -> str:
        """Generate a hash for the URL to use as unique identifier"""
        return hashlib.md5(url.encode()).hexdigest()

    def save_articles(self, articles: List[Dict]) -> int:
        """Save articles to database, return number of new articles added"""
        if not articles:
            return 0
            
        new_articles = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for article in articles:
                url_hash = self._generate_url_hash(article['url'])
                
                try:
                    cursor.execute('''
                        INSERT INTO news_articles 
                        (title, url, content, source, article_date, scraped_at, url_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article['title'],
                        article['url'], 
                        article.get('content', ''),
                        article['source'],
                        article.get('date', ''),
                        datetime.now().isoformat(),
                        url_hash
                    ))
                    new_articles += 1
                    
                except sqlite3.IntegrityError:
                    # Article already exists (duplicate URL)
                    pass
            
            conn.commit()
        
        return new_articles

    def get_unprocessed_articles(self, limit: Optional[int] = None) -> List[Dict]:
        """Get articles that haven't been processed yet"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM news_articles 
                WHERE processed = FALSE 
                ORDER BY scraped_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]

    def mark_as_processed(self, article_ids: List[int], summaries: List[str] = None):
        """Mark articles as processed and optionally save summaries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for i, article_id in enumerate(article_ids):
                summary = summaries[i] if summaries and i < len(summaries) else None
                cursor.execute('''
                    UPDATE news_articles 
                    SET processed = TRUE, processed_at = ?, summary = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), summary, article_id))
            
            conn.commit()

    def get_recent_articles(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Get articles from the last N days"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM news_articles 
                WHERE datetime(scraped_at) >= datetime('now', '-{} days')
                ORDER BY scraped_at DESC
                LIMIT ?
            '''.format(days), (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_articles_by_source(self, source: str, limit: int = 20) -> List[Dict]:
        """Get articles from a specific source"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM news_articles 
                WHERE source = ?
                ORDER BY scraped_at DESC
                LIMIT ?
            ''', (source, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def article_exists(self, url: str) -> bool:
        """Check if an article with the given URL already exists"""
        url_hash = self._generate_url_hash(url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM news_articles WHERE url_hash = ?', (url_hash,))
            return cursor.fetchone() is not None

    def get_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute('SELECT COUNT(*) FROM news_articles')
            total = cursor.fetchone()[0]
            
            # Processed articles
            cursor.execute('SELECT COUNT(*) FROM news_articles WHERE processed = TRUE')
            processed = cursor.fetchone()[0]
            
            # Articles by source
            cursor.execute('''
                SELECT source, COUNT(*) as count 
                FROM news_articles 
                GROUP BY source 
                ORDER BY count DESC
            ''')
            by_source = dict(cursor.fetchall())
            
            # Recent articles (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM news_articles 
                WHERE datetime(scraped_at) >= datetime('now', '-1 day')
            ''')
            recent = cursor.fetchone()[0]
            
            return {
                'total_articles': total,
                'processed_articles': processed,
                'unprocessed_articles': total - processed,
                'articles_by_source': by_source,
                'articles_last_24h': recent
            }

    def cleanup_old_articles(self, days: int = 30):
        """Remove articles older than N days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM news_articles 
                WHERE datetime(scraped_at) < datetime('now', '-{} days')
            '''.format(days))
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted