import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import os
import json
import numpy as np
import sqlite_vec


class NewsDatabase:
    def __init__(self, db_path: str = 'sumo_news.db'):
        self.db_path = db_path
        self.init_database()
    
    def _get_connection(self):
        """Get a SQLite connection with sqlite-vec extension loaded"""
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return conn

    def init_database(self):
        """Initialize the database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # First, check if this is a new database or existing one
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_articles'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new enhanced table
                cursor.execute('''
                    CREATE TABLE news_articles (
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
                        processed_at TEXT,
                        
                        -- Vector fields
                        content_embedding BLOB,
                        title_embedding BLOB,
                        embedding_model TEXT,
                        embedding_created_at TEXT,
                        
                        -- Semantic analysis fields
                        semantic_hash TEXT,
                        topics TEXT,
                        entities TEXT,
                        
                        -- Reference tracking
                        related_articles TEXT
                    )
                ''')
            else:
                # Add new columns to existing table if they don't exist
                self._add_columns_if_missing(cursor)
            
            # Create article relationships table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_article_id INTEGER NOT NULL,
                    target_article_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL,
                    confidence_score REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_article_id) REFERENCES news_articles(id),
                    FOREIGN KEY (target_article_id) REFERENCES news_articles(id),
                    UNIQUE(source_article_id, target_article_id, relationship_type)
                )
            ''')
            
            # Create tags table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    description TEXT,
                    color TEXT,
                    created_at TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create article_tags junction table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    confidence_score REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    created_by TEXT DEFAULT 'system',
                    FOREIGN KEY (article_id) REFERENCES news_articles(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                    UNIQUE(article_id, tag_id)
                )
            ''')
            
            # Create sumo_tips table for educational content
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sumo_tips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    difficulty_level TEXT DEFAULT 'beginner',
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    usage_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create vector similarity virtual tables
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS article_content_vectors USING vec0(
                    article_id INTEGER PRIMARY KEY,
                    content_embedding FLOAT[1536]
                )
            ''')
            
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS article_title_vectors USING vec0(
                    article_id INTEGER PRIMARY KEY,
                    title_embedding FLOAT[1536]
                )
            ''')
            
            # Create indexes for better performance (only for existing columns)
            self._create_indexes_safely(cursor)
            
            conn.commit()
    
    def _add_columns_if_missing(self, cursor):
        """Add new columns to existing table if they don't exist"""
        # Get existing columns
        cursor.execute("PRAGMA table_info(news_articles)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Define new columns to add
        new_columns = [
            ('content_embedding', 'BLOB'),
            ('title_embedding', 'BLOB'),
            ('embedding_model', 'TEXT'),
            ('embedding_created_at', 'TEXT'),
            ('semantic_hash', 'TEXT'),
            ('topics', 'TEXT'),
            ('entities', 'TEXT'),
            ('related_articles', 'TEXT')
        ]
        
        # Add missing columns
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE news_articles ADD COLUMN {column_name} {column_type}')
                    print(f'Added column: {column_name}')
                except Exception as e:
                    print(f'Note: Could not add column {column_name}: {e}')
    
    def _create_indexes_safely(self, cursor):
        """Create indexes, checking for column existence first"""
        # Basic indexes that should always exist
        basic_indexes = [
            ('idx_url_hash', 'url_hash'),
            ('idx_source', 'source'),
            ('idx_scraped_at', 'scraped_at'),
            ('idx_processed', 'processed')
        ]
        
        for index_name, column_name in basic_indexes:
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON news_articles({column_name})')
            except Exception as e:
                print(f'Note: Could not create index {index_name}: {e}')
        
        # Check for new columns before creating their indexes
        cursor.execute("PRAGMA table_info(news_articles)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # New column indexes
        new_indexes = [
            ('idx_embedding_model', 'embedding_model'),
            ('idx_semantic_hash', 'semantic_hash'),
        ]
        
        for index_name, column_name in new_indexes:
            if column_name in existing_columns:
                try:
                    cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON news_articles({column_name})')
                except Exception as e:
                    print(f'Note: Could not create index {index_name}: {e}')
        
        # Relationship table indexes
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationship_type ON article_relationships(relationship_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_confidence_score ON article_relationships(confidence_score)')
        except Exception as e:
            print(f'Note: Could not create relationship indexes: {e}')
        
        # Tag table indexes
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tag_name ON tags(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tag_category ON tags(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tag_usage_count ON tags(usage_count)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_article_tags_article ON article_tags(article_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_article_tags_tag ON article_tags(tag_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_article_tags_confidence ON article_tags(confidence_score)')
        except Exception as e:
            print(f'Note: Could not create tag indexes: {e}')
        
        # Sumo tips table indexes
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sumo_tips_category ON sumo_tips(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sumo_tips_difficulty ON sumo_tips(difficulty_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sumo_tips_usage ON sumo_tips(usage_count)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sumo_tips_last_used ON sumo_tips(last_used_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sumo_tips_active ON sumo_tips(is_active)')
        except Exception as e:
            print(f'Note: Could not create sumo tips indexes: {e}')

    def _generate_url_hash(self, url: str) -> str:
        """Generate a hash for the URL to use as unique identifier"""
        return hashlib.md5(url.encode()).hexdigest()

    def save_articles(self, articles: List[Dict]) -> int:
        """Save articles to database, return number of new articles added"""
        if not articles:
            return 0
            
        new_articles = 0
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
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
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM news_articles WHERE url_hash = ?', (url_hash,))
            return cursor.fetchone() is not None

    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM news_articles 
                WHERE datetime(scraped_at) < datetime('now', '-{} days')
            '''.format(days))
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted
    
    def remove_duplicate_articles(self, similarity_threshold: float = 0.95) -> Dict:
        """Remove duplicate articles based on semantic similarity and URL matching"""
        results = {
            'url_duplicates_removed': 0,
            'semantic_duplicates_removed': 0,
            'total_removed': 0,
            'errors': 0
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Step 1: Remove URL-based duplicates (keep the newest)
            cursor.execute('''
                WITH duplicates AS (
                    SELECT url_hash, MIN(id) as keep_id
                    FROM news_articles 
                    GROUP BY url_hash 
                    HAVING COUNT(*) > 1
                )
                DELETE FROM news_articles 
                WHERE id IN (
                    SELECT na.id 
                    FROM news_articles na
                    JOIN duplicates d ON na.url_hash = d.url_hash
                    WHERE na.id != d.keep_id
                )
            ''')
            
            url_duplicates = cursor.rowcount
            results['url_duplicates_removed'] = url_duplicates
            
            # Step 2: Remove semantic duplicates (same semantic_hash)
            cursor.execute('''
                WITH semantic_duplicates AS (
                    SELECT semantic_hash, MIN(id) as keep_id
                    FROM news_articles 
                    WHERE semantic_hash IS NOT NULL
                    GROUP BY semantic_hash 
                    HAVING COUNT(*) > 1
                )
                DELETE FROM news_articles 
                WHERE id IN (
                    SELECT na.id 
                    FROM news_articles na
                    JOIN semantic_duplicates sd ON na.semantic_hash = sd.semantic_hash
                    WHERE na.id != sd.keep_id
                )
            ''')
            
            semantic_duplicates = cursor.rowcount
            results['semantic_duplicates_removed'] = semantic_duplicates
            
            # Clean up orphaned vector entries
            try:
                cursor.execute('''
                    DELETE FROM article_content_vectors 
                    WHERE article_id NOT IN (SELECT id FROM news_articles)
                ''')
                
                cursor.execute('''
                    DELETE FROM article_title_vectors 
                    WHERE article_id NOT IN (SELECT id FROM news_articles)
                ''')
                
                cursor.execute('''
                    DELETE FROM article_relationships 
                    WHERE source_article_id NOT IN (SELECT id FROM news_articles)
                       OR target_article_id NOT IN (SELECT id FROM news_articles)
                ''')
            except Exception as e:
                print(f"Error cleaning up vector tables: {e}")
                results['errors'] += 1
            
            conn.commit()
            
            results['total_removed'] = url_duplicates + semantic_duplicates
            return results
    
    def get_duplicate_analysis(self) -> Dict:
        """Analyze potential duplicates in the database"""
        analysis = {
            'url_duplicates': 0,
            'semantic_duplicates': 0,
            'similar_titles': [],
            'total_articles': 0
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute('SELECT COUNT(*) FROM news_articles')
            analysis['total_articles'] = cursor.fetchone()[0]
            
            # URL duplicates
            cursor.execute('''
                SELECT COUNT(*) FROM (
                    SELECT url_hash 
                    FROM news_articles 
                    GROUP BY url_hash 
                    HAVING COUNT(*) > 1
                )
            ''')
            analysis['url_duplicates'] = cursor.fetchone()[0]
            
            # Semantic duplicates
            cursor.execute('''
                SELECT COUNT(*) FROM (
                    SELECT semantic_hash 
                    FROM news_articles 
                    WHERE semantic_hash IS NOT NULL
                    GROUP BY semantic_hash 
                    HAVING COUNT(*) > 1
                )
            ''')
            analysis['semantic_duplicates'] = cursor.fetchone()[0]
            
            # Find similar titles (potential duplicates)
            cursor.execute('''
                SELECT title, COUNT(*) as count
                FROM news_articles
                GROUP BY LOWER(title)
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            analysis['similar_titles'] = [
                {'title': row[0], 'count': row[1]} 
                for row in cursor.fetchall()
            ]
        
        return analysis
    
    def optimize_database(self) -> Dict:
        """Optimize database by removing duplicates and cleaning up"""
        print("Optimizing database...")
        
        # Get analysis before cleanup
        before_analysis = self.get_duplicate_analysis()
        print(f"Before cleanup: {before_analysis['total_articles']} articles")
        
        # Remove duplicates
        duplicate_results = self.remove_duplicate_articles()
        
        # Get analysis after cleanup
        after_analysis = self.get_duplicate_analysis()
        print(f"After cleanup: {after_analysis['total_articles']} articles")
        
        # Vacuum database to reclaim space
        try:
            with self._get_connection() as conn:
                conn.execute('VACUUM')
                print("Database vacuumed successfully")
        except Exception as e:
            print(f"Error vacuuming database: {e}")
        
        return {
            'before': before_analysis,
            'after': after_analysis,
            'removed': duplicate_results,
            'space_saved': before_analysis['total_articles'] - after_analysis['total_articles']
        }
    
    # Vector database methods
    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """Convert embedding list to bytes for storage"""
        return np.array(embedding, dtype=np.float32).tobytes()
    
    def _deserialize_embedding(self, data: bytes) -> List[float]:
        """Convert bytes back to embedding list"""
        return np.frombuffer(data, dtype=np.float32).tolist()
    
    def save_article_with_embeddings(self, article: Dict, 
                                   content_embedding: Optional[List[float]] = None,
                                   title_embedding: Optional[List[float]] = None,
                                   embedding_model: str = 'text-embedding-3-small',
                                   topics: List[str] = None,
                                   entities: List[str] = None) -> Optional[int]:
        """Save article with vector embeddings and semantic data"""
        url_hash = self._generate_url_hash(article['url'])
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Generate semantic hash from content
                content_text = f"{article['title']} {article.get('content', '')}"
                semantic_hash = hashlib.sha256(content_text.encode()).hexdigest()[:16]
                
                cursor.execute('''
                    INSERT INTO news_articles 
                    (title, url, content, source, article_date, scraped_at, url_hash,
                     content_embedding, title_embedding, embedding_model, embedding_created_at,
                     semantic_hash, topics, entities)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['title'],
                    article['url'], 
                    article.get('content', ''),
                    article['source'],
                    article.get('date', ''),
                    datetime.now().isoformat(),
                    url_hash,
                    self._serialize_embedding(content_embedding) if content_embedding else None,
                    self._serialize_embedding(title_embedding) if title_embedding else None,
                    embedding_model,
                    datetime.now().isoformat() if content_embedding or title_embedding else None,
                    semantic_hash,
                    json.dumps(topics) if topics else None,
                    json.dumps(entities) if entities else None
                ))
                
                article_id = cursor.lastrowid
                
                # Save embeddings to vector tables if provided
                if content_embedding and article_id:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO article_content_vectors 
                            (article_id, content_embedding) VALUES (?, ?)
                        ''', (article_id, content_embedding))
                    except Exception as e:
                        print(f"Error saving content embedding: {e}")
                
                if title_embedding and article_id:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO article_title_vectors 
                            (article_id, title_embedding) VALUES (?, ?)
                        ''', (article_id, title_embedding))
                    except Exception as e:
                        print(f"Error saving title embedding: {e}")
                
                conn.commit()
                return article_id
                
            except sqlite3.IntegrityError:
                # Article already exists
                return None
    
    def find_similar_articles(self, embedding: List[float], 
                            table_type: str = 'content',
                            similarity_threshold: float = 0.8,
                            limit: int = 10) -> List[Dict]:
        """Find similar articles using vector similarity search"""
        table_name = f'article_{table_type}_vectors'
        
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if there are any vectors in the table first
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                vector_count = cursor.fetchone()[0]
                
                if vector_count == 0:
                    return []
                
                # Convert embedding to proper format for sqlite-vec
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                # Use sqlite-vec KNN search with proper syntax
                query = f'''
                    SELECT 
                        av.article_id,
                        distance,
                        na.title,
                        na.url,
                        na.source,
                        na.article_date,
                        na.summary
                    FROM {table_name} av
                    JOIN news_articles na ON av.article_id = na.id
                    WHERE {table_type}_embedding MATCH ?
                    ORDER BY distance
                    LIMIT ?
                '''
                
                cursor.execute(query, (embedding_str, limit))
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    row_dict = dict(row)
                    # Only include results within similarity threshold
                    if row_dict.get('distance', 1.0) <= (1.0 - similarity_threshold):
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def check_semantic_duplicate(self, content: str, title: str = '') -> Optional[Dict]:
        """Check for semantic duplicates using content hash"""
        content_text = f"{title} {content}"
        semantic_hash = hashlib.sha256(content_text.encode()).hexdigest()[:16]
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM news_articles 
                WHERE semantic_hash = ?
                LIMIT 1
            ''', (semantic_hash,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_article_relationship(self, source_id: int, target_id: int, 
                               relationship_type: str, confidence_score: float):
        """Add a relationship between two articles"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO article_relationships 
                    (source_article_id, target_article_id, relationship_type, 
                     confidence_score, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (source_id, target_id, relationship_type, 
                      confidence_score, datetime.now().isoformat()))
                
                conn.commit()
                
            except sqlite3.Error as e:
                print(f"Error adding relationship: {e}")
    
    def get_article_relationships(self, article_id: int, 
                                relationship_types: List[str] = None) -> List[Dict]:
        """Get relationships for a specific article"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            where_clause = "WHERE (ar.source_article_id = ? OR ar.target_article_id = ?)"
            params = [article_id, article_id]
            
            if relationship_types:
                placeholders = ','.join('?' * len(relationship_types))
                where_clause += f" AND ar.relationship_type IN ({placeholders})"
                params.extend(relationship_types)
            
            cursor.execute(f'''
                SELECT 
                    ar.*,
                    na.title as related_title,
                    na.url as related_url,
                    na.source as related_source,
                    na.article_date as related_date
                FROM article_relationships ar
                JOIN news_articles na ON (
                    CASE 
                        WHEN ar.source_article_id = ? THEN ar.target_article_id
                        ELSE ar.source_article_id
                    END = na.id
                )
                {where_clause}
                ORDER BY ar.confidence_score DESC
            ''', [article_id] + params)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_article_embeddings(self, article_id: int,
                                content_embedding: Optional[List[float]] = None,
                                title_embedding: Optional[List[float]] = None,
                                embedding_model: str = 'text-embedding-3-small'):
        """Update embeddings for an existing article"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Update main table
            cursor.execute('''
                UPDATE news_articles 
                SET content_embedding = ?, title_embedding = ?, 
                    embedding_model = ?, embedding_created_at = ?
                WHERE id = ?
            ''', (
                self._serialize_embedding(content_embedding) if content_embedding else None,
                self._serialize_embedding(title_embedding) if title_embedding else None,
                embedding_model,
                datetime.now().isoformat(),
                article_id
            ))
            
            # Update vector tables
            if content_embedding:
                cursor.execute('''
                    INSERT OR REPLACE INTO article_content_vectors 
                    (article_id, content_embedding) VALUES (?, ?)
                ''', (article_id, content_embedding))
            
            if title_embedding:
                cursor.execute('''
                    INSERT OR REPLACE INTO article_title_vectors 
                    (article_id, title_embedding) VALUES (?, ?)
                ''', (article_id, title_embedding))
            
            conn.commit()
    
    def get_articles_without_embeddings(self, limit: Optional[int] = None) -> List[Dict]:
        """Get articles that don't have embeddings yet"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM news_articles 
                WHERE content_embedding IS NULL OR title_embedding IS NULL
                ORDER BY scraped_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]