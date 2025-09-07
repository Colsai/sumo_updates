"""
Tag Management System

Handles tagging functionality for articles in the sumo news database.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import json


class TagManager:
    def __init__(self, database):
        """Initialize with a NewsDatabase instance"""
        self.db = database
    
    def create_tag(self, name: str, category: str, description: str = None, 
                  color: str = None) -> Optional[int]:
        """Create a new tag"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tags (name, category, description, color, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name.lower().strip(), category.lower(), description, color, 
                      datetime.now().isoformat()))
                
                tag_id = cursor.lastrowid
                conn.commit()
                print(f"Created tag: {name} ({category})")
                return tag_id
                
        except sqlite3.IntegrityError:
            # Tag already exists
            return self.get_tag_id(name)
        except Exception as e:
            print(f"Error creating tag {name}: {e}")
            return None
    
    def get_tag_id(self, name: str) -> Optional[int]:
        """Get tag ID by name"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tags WHERE name = ?', (name.lower().strip(),))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_or_create_tag(self, name: str, category: str, description: str = None,
                         color: str = None) -> int:
        """Get existing tag ID or create new tag"""
        tag_id = self.get_tag_id(name)
        if tag_id is None:
            tag_id = self.create_tag(name, category, description, color)
        return tag_id
    
    def add_tags_to_article(self, article_id: int, tag_names: List[str], 
                           confidence_scores: List[float] = None,
                           created_by: str = 'system') -> int:
        """Add multiple tags to an article"""
        if not tag_names:
            return 0
        
        added_count = 0
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            for i, tag_name in enumerate(tag_names):
                if not tag_name or not tag_name.strip():
                    continue
                    
                confidence = confidence_scores[i] if confidence_scores and i < len(confidence_scores) else 1.0
                
                # Get or create tag
                tag_id = self.get_tag_id(tag_name)
                if not tag_id:
                    # Auto-categorize tag based on patterns
                    category = self.auto_categorize_tag(tag_name)
                    tag_id = self.create_tag(tag_name, category)
                
                if tag_id:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO article_tags 
                            (article_id, tag_id, confidence_score, created_at, created_by)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (article_id, tag_id, confidence, datetime.now().isoformat(), created_by))
                        
                        if cursor.rowcount > 0:
                            # Update tag usage count
                            cursor.execute('''
                                UPDATE tags SET usage_count = usage_count + 1 
                                WHERE id = ?
                            ''', (tag_id,))
                            added_count += 1
                            
                    except Exception as e:
                        print(f"Error adding tag {tag_name} to article {article_id}: {e}")
            
            conn.commit()
        
        return added_count
    
    def auto_categorize_tag(self, tag_name: str) -> str:
        """Auto-categorize tags based on patterns"""
        tag_lower = tag_name.lower()
        
        # Tournament patterns
        if any(term in tag_lower for term in ['basho', 'tournament', 'championship', 'grand']):
            return 'tournament'
        
        # Wrestler rank patterns  
        if any(term in tag_lower for term in ['yokozuna', 'ozeki', 'sekiwake', 'komusubi', 'maegashira']):
            return 'rank'
        
        # Wrestler name patterns (common sumo names)
        if any(term in tag_lower for term in ['terunofuji', 'onosato', 'hoshoryu', 'kotonowaka', 'kirishima', 'mitakeumi']):
            return 'wrestler'
        
        # Event patterns
        if any(term in tag_lower for term in ['promotion', 'retirement', 'injury', 'victory', 'defeat', 'charity']):
            return 'event'
        
        # Location patterns
        if any(term in tag_lower for term in ['tokyo', 'osaka', 'nagoya', 'kyushu', 'london', 'japan', 'noto']):
            return 'location'
        
        # Organization patterns
        if any(term in tag_lower for term in ['jsa', 'ifs', 'association', 'federation']):
            return 'organization'
        
        # Content type patterns
        if any(term in tag_lower for term in ['interview', 'schedule', 'results', 'news', 'highlights', 'banzuke']):
            return 'content-type'
        
        # Date patterns
        if any(char.isdigit() for char in tag_lower) and any(term in tag_lower for term in ['2024', '2025', '2026']):
            return 'date'
        
        # Default category
        return 'general'
    
    def get_article_tags(self, article_id: int) -> List[Dict]:
        """Get all tags for a specific article"""
        with self.db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT t.id, t.name, t.category, t.description, t.color,
                       at.confidence_score, at.created_at, at.created_by
                FROM tags t
                JOIN article_tags at ON t.id = at.tag_id
                WHERE at.article_id = ?
                ORDER BY at.confidence_score DESC, t.name
            ''', (article_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_articles_by_tag(self, tag_name: str, limit: int = 50) -> List[Dict]:
        """Get all articles with a specific tag"""
        with self.db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT na.*, at.confidence_score
                FROM news_articles na
                JOIN article_tags at ON na.id = at.article_id
                JOIN tags t ON at.tag_id = t.id
                WHERE t.name = ?
                ORDER BY na.scraped_at DESC
                LIMIT ?
            ''', (tag_name.lower().strip(), limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_articles_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get all articles with tags in a specific category"""
        with self.db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT na.*, t.name as tag_name, at.confidence_score
                FROM news_articles na
                JOIN article_tags at ON na.id = at.article_id
                JOIN tags t ON at.tag_id = t.id
                WHERE t.category = ?
                ORDER BY na.scraped_at DESC
                LIMIT ?
            ''', (category.lower(), limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_tag_statistics(self) -> Dict:
        """Get statistics about tag usage"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total tags
            cursor.execute('SELECT COUNT(*) FROM tags')
            total_tags = cursor.fetchone()[0]
            
            # Tags by category
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM tags
                GROUP BY category
                ORDER BY count DESC
            ''')
            by_category = dict(cursor.fetchall())
            
            # Most used tags
            cursor.execute('''
                SELECT name, category, usage_count
                FROM tags
                ORDER BY usage_count DESC
                LIMIT 20
            ''')
            most_used = [{'name': row[0], 'category': row[1], 'count': row[2]} 
                        for row in cursor.fetchall()]
            
            # Articles with tags
            cursor.execute('''
                SELECT COUNT(DISTINCT article_id) FROM article_tags
            ''')
            articles_with_tags = cursor.fetchone()[0]
            
            return {
                'total_tags': total_tags,
                'tags_by_category': by_category,
                'most_used_tags': most_used,
                'articles_with_tags': articles_with_tags
            }
    
    def search_articles_by_tags(self, tag_names: List[str], 
                               match_type: str = 'any', limit: int = 50) -> List[Dict]:
        """Search articles by multiple tags (AND/OR logic)"""
        if not tag_names:
            return []
        
        with self.db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if match_type.lower() == 'all':
                # Must have ALL tags (AND logic)
                placeholders = ','.join('?' * len(tag_names))
                cursor.execute(f'''
                    SELECT na.*, COUNT(DISTINCT t.id) as tag_matches
                    FROM news_articles na
                    JOIN article_tags at ON na.id = at.article_id
                    JOIN tags t ON at.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                    GROUP BY na.id
                    HAVING tag_matches = ?
                    ORDER BY na.scraped_at DESC
                    LIMIT ?
                ''', tag_names + [len(tag_names), limit])
            else:
                # Must have ANY tag (OR logic)
                placeholders = ','.join('?' * len(tag_names))
                cursor.execute(f'''
                    SELECT DISTINCT na.*
                    FROM news_articles na
                    JOIN article_tags at ON na.id = at.article_id
                    JOIN tags t ON at.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                    ORDER BY na.scraped_at DESC
                    LIMIT ?
                ''', tag_names + [limit])
            
            return [dict(row) for row in cursor.fetchall()]
    
    def remove_tag_from_article(self, article_id: int, tag_name: str) -> bool:
        """Remove a specific tag from an article"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM article_tags 
                    WHERE article_id = ? AND tag_id = (
                        SELECT id FROM tags WHERE name = ?
                    )
                ''', (article_id, tag_name.lower().strip()))
                
                if cursor.rowcount > 0:
                    # Decrease usage count
                    cursor.execute('''
                        UPDATE tags SET usage_count = usage_count - 1 
                        WHERE name = ? AND usage_count > 0
                    ''', (tag_name.lower().strip(),))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error removing tag {tag_name} from article {article_id}: {e}")
        
        return False
    
    def get_all_tags(self, category: str = None, limit: int = 100) -> List[Dict]:
        """Get all tags, optionally filtered by category"""
        with self.db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM tags 
                    WHERE category = ? 
                    ORDER BY usage_count DESC, name
                    LIMIT ?
                ''', (category.lower(), limit))
            else:
                cursor.execute('''
                    SELECT * FROM tags 
                    ORDER BY usage_count DESC, name
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def generate_smart_tags_from_content(self, title: str, content: str, entities: List[str] = None) -> List[str]:
        """Generate smart tags from article content using pattern matching"""
        tags = []
        text = f"{title} {content}".lower()
        
        # Tournament/Event detection
        if 'basho' in text or 'tournament' in text:
            if 'september' in text or '09' in text:
                tags.append('september-basho')
            elif 'autumn' in text:
                tags.append('autumn-tournament')
            else:
                tags.append('tournament')
        
        # Rank detection
        rank_patterns = {
            'yokozuna': 'yokozuna',
            'ozeki': 'ozeki', 
            'sekiwake': 'sekiwake',
            'komusubi': 'komusubi',
            'maegashira': 'maegashira'
        }
        
        for pattern, tag in rank_patterns.items():
            if pattern in text:
                tags.append(tag)
        
        # Event type detection
        if 'promoted' in text or 'promotion' in text:
            tags.append('promotion')
        if 'retired' in text or 'retirement' in text:
            tags.append('retirement')
        if 'injured' in text or 'injury' in text:
            tags.append('injury')
        if 'victory' in text or 'win' in text or 'champion' in text:
            tags.append('victory')
        if 'charity' in text or 'support' in text:
            tags.append('charity')
        
        # Location detection
        location_patterns = {
            'tokyo': 'tokyo',
            'osaka': 'osaka', 
            'nagoya': 'nagoya',
            'kyushu': 'kyushu',
            'london': 'london',
            'noto': 'noto-peninsula'
        }
        
        for pattern, tag in location_patterns.items():
            if pattern in text:
                tags.append(tag)
        
        # Content type detection
        if 'interview' in text:
            tags.append('interview')
        if 'schedule' in text:
            tags.append('schedule')
        if 'banzuke' in text:
            tags.append('banzuke')
        if 'highlights' in text:
            tags.append('highlights')
        if 'results' in text:
            tags.append('results')
        
        # Add entity-based tags
        if entities:
            for entity in entities[:5]:  # Limit to top 5 entities
                if entity and len(entity.strip()) > 2:
                    tags.append(entity.lower().strip())
        
        # Date tags
        if '2025' in text:
            tags.append('2025')
        if '2024' in text:
            tags.append('2024')
        
        # Remove duplicates and clean
        unique_tags = []
        for tag in tags:
            clean_tag = tag.strip().lower()
            if clean_tag and clean_tag not in unique_tags and len(clean_tag) > 1:
                unique_tags.append(clean_tag)
        
        return unique_tags[:15]  # Limit to 15 tags max