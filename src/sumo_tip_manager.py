"""
Sumo Tip Manager

Manages educational sumo wrestling facts and tips for the "Bite-sized Sumo" 
section in email newsletters.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random


class SumoTipManager:
    def __init__(self, database):
        """Initialize with a NewsDatabase instance"""
        self.db = database
        self._ensure_initial_tips()
    
    def add_tip(self, title: str, content: str, category: str, 
               difficulty_level: str = 'beginner') -> int:
        """Add a new sumo tip to the database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sumo_tips 
                    (title, content, category, difficulty_level, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, content, category.lower(), difficulty_level.lower(), 
                      datetime.now().isoformat()))
                
                tip_id = cursor.lastrowid
                conn.commit()
                return tip_id
                
        except Exception as e:
            print(f"Error adding tip: {e}")
            return None
    
    def get_unused_tip(self, category: str = None, 
                      difficulty_level: str = None,
                      days_since_last_use: int = 30) -> Optional[Dict]:
        """Get a tip that hasn't been used recently"""
        with self.db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query with optional filters
            where_clauses = ['is_active = 1']
            params = []
            
            if category:
                where_clauses.append('category = ?')
                params.append(category.lower())
            
            if difficulty_level:
                where_clauses.append('difficulty_level = ?')
                params.append(difficulty_level.lower())
            
            # Prefer tips that haven't been used recently or at all
            cutoff_date = (datetime.now() - timedelta(days=days_since_last_use)).isoformat()
            where_clauses.append('(last_used_at IS NULL OR last_used_at < ?)')
            params.append(cutoff_date)
            
            where_clause = ' AND '.join(where_clauses)
            
            cursor.execute(f'''
                SELECT * FROM sumo_tips 
                WHERE {where_clause}
                ORDER BY 
                    CASE WHEN last_used_at IS NULL THEN 0 ELSE 1 END,
                    usage_count ASC,
                    RANDOM()
                LIMIT 1
            ''', params)
            
            tip = cursor.fetchone()
            if tip:
                return dict(tip)
            
            # If no unused tips, get least recently used
            where_clauses = ['is_active = 1']
            params = []
            
            if category:
                where_clauses.append('category = ?')
                params.append(category.lower())
            
            if difficulty_level:
                where_clauses.append('difficulty_level = ?')
                params.append(difficulty_level.lower())
            
            where_clause = ' AND '.join(where_clauses)
            
            cursor.execute(f'''
                SELECT * FROM sumo_tips 
                WHERE {where_clause}
                ORDER BY 
                    CASE WHEN last_used_at IS NULL THEN 0 ELSE 1 END,
                    last_used_at ASC,
                    usage_count ASC
                LIMIT 1
            ''', params)
            
            tip = cursor.fetchone()
            return dict(tip) if tip else None
    
    def mark_tip_as_used(self, tip_id: int):
        """Mark a tip as used, updating usage statistics"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sumo_tips 
                    SET last_used_at = ?, usage_count = usage_count + 1
                    WHERE id = ?
                ''', (datetime.now().isoformat(), tip_id))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error marking tip as used: {e}")
    
    def get_tip_statistics(self) -> Dict:
        """Get statistics about sumo tips"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total tips
            cursor.execute('SELECT COUNT(*) FROM sumo_tips WHERE is_active = 1')
            total_tips = cursor.fetchone()[0]
            
            # Tips by category
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM sumo_tips 
                WHERE is_active = 1
                GROUP BY category
                ORDER BY count DESC
            ''')
            by_category = dict(cursor.fetchall())
            
            # Most used tips
            cursor.execute('''
                SELECT title, category, usage_count
                FROM sumo_tips
                WHERE is_active = 1
                ORDER BY usage_count DESC
                LIMIT 10
            ''')
            most_used = [{'title': row[0], 'category': row[1], 'count': row[2]} 
                        for row in cursor.fetchall()]
            
            # Unused tips
            cursor.execute('SELECT COUNT(*) FROM sumo_tips WHERE last_used_at IS NULL AND is_active = 1')
            unused_count = cursor.fetchone()[0]
            
            return {
                'total_tips': total_tips,
                'tips_by_category': by_category,
                'most_used_tips': most_used,
                'unused_tips': unused_count
            }
    
    def get_all_tips(self, category: str = None, limit: int = 100) -> List[Dict]:
        """Get all tips, optionally filtered by category"""
        with self.db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM sumo_tips 
                    WHERE category = ? AND is_active = 1
                    ORDER BY usage_count ASC, title
                    LIMIT ?
                ''', (category.lower(), limit))
            else:
                cursor.execute('''
                    SELECT * FROM sumo_tips 
                    WHERE is_active = 1
                    ORDER BY category, usage_count ASC, title
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _ensure_initial_tips(self):
        """Ensure database has initial collection of sumo tips"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sumo_tips')
            tip_count = cursor.fetchone()[0]
            
            if tip_count == 0:
                print("Adding initial sumo tips to database...")
                self._add_initial_tips()
    
    def _add_initial_tips(self):
        """Add initial collection of sumo tips"""
        initial_tips = [
            # History tips
            {
                'title': 'Ancient Origins',
                'content': 'Sumo wrestling dates back over 1,500 years and originated as a Shinto ritual to entertain the gods and ensure a good harvest. The first recorded sumo match was in 23 BC!',
                'category': 'history',
                'difficulty': 'beginner'
            },
            {
                'title': 'The Yokozuna Tradition',
                'content': 'The title "Yokozuna" means "horizontal rope" and refers to the sacred rope worn during ceremonies. Only 75 wrestlers in history have achieved this highest rank.',
                'category': 'ranks',
                'difficulty': 'beginner'
            },
            {
                'title': 'Salt Purification Ritual',
                'content': 'Wrestlers throw salt (shio) into the ring before matches to purify the sacred space and ward off evil spirits. Up to 45kg of salt is used per tournament day!',
                'category': 'rituals',
                'difficulty': 'beginner'
            },
            
            # Techniques tips
            {
                'title': 'Winning Techniques: Kimarite',
                'content': 'There are 82 official winning techniques (kimarite) in sumo. The most common is "yorikiri" - carrying your opponent out of the ring while holding their belt.',
                'category': 'techniques',
                'difficulty': 'intermediate'
            },
            {
                'title': 'The Power of the Tachiai',
                'content': 'The initial charge (tachiai) often determines the match outcome. Wrestlers can reach speeds of 25+ mph in just the first few steps!',
                'category': 'techniques',
                'difficulty': 'beginner'
            },
            
            # Rules and traditions
            {
                'title': 'The Sacred Dohyo',
                'content': 'The sumo ring (dohyo) is made of clay and considered sacred. It\'s rebuilt for each tournament and blessed by Shinto priests.',
                'category': 'traditions',
                'difficulty': 'beginner'
            },
            {
                'title': 'Topknot Significance',
                'content': 'The traditional topknot (chonmage) isn\'t just for style - it once protected samurai heads when wearing helmets. In sumo, different styles indicate rank.',
                'category': 'traditions',
                'difficulty': 'intermediate'
            },
            
            # Tournament facts
            {
                'title': 'Six Grand Tournaments',
                'content': 'There are six grand tournaments (honbasho) per year: January, March, May (Tokyo), July (Nagoya), September (Tokyo), and November (Kyushu).',
                'category': 'tournaments',
                'difficulty': 'beginner'
            },
            {
                'title': 'Perfect Records Are Rare',
                'content': 'A perfect 15-0 tournament record (zensho-yusho) has only been achieved 84 times in the modern era. The last was Hakuho in 2017.',
                'category': 'tournaments',
                'difficulty': 'intermediate'
            },
            
            # Cultural facts
            {
                'title': 'Sumo Stable Life',
                'content': 'Wrestlers live together in training stables (heya) where junior wrestlers cook, clean, and serve senior members. It\'s like a traditional Japanese family system.',
                'category': 'culture',
                'difficulty': 'beginner'
            },
            {
                'title': 'The Gyoji Referee',
                'content': 'Sumo referees (gyoji) carry a ceremonial dagger as a symbol that they\'re prepared to commit seppuku if they make a serious judging error!',
                'category': 'culture',
                'difficulty': 'intermediate'
            },
            
            # Famous wrestlers
            {
                'title': 'Hakuho\'s Record Reign',
                'content': 'Hakuho holds the record for most tournament victories (45) and most wins overall (1,187). He was yokozuna for 14 years!',
                'category': 'wrestlers',
                'difficulty': 'intermediate'
            },
            {
                'title': 'International Champions',
                'content': 'While sumo originated in Japan, wrestlers from Mongolia, Hawaii, Bulgaria, and other countries have become yokozuna and champions.',
                'category': 'wrestlers',
                'difficulty': 'beginner'
            },
            
            # Fun facts
            {
                'title': 'Sumo Size Myths',
                'content': 'Not all sumo wrestlers are huge! Some successful wrestlers weigh under 300 pounds and rely on speed and technique rather than pure size.',
                'category': 'facts',
                'difficulty': 'beginner'
            },
            {
                'title': 'The Chanko-nabe Diet',
                'content': 'Sumo wrestlers eat chanko-nabe (hot pot stew) containing meat, fish, vegetables, and rice. They eat only twice a day but in massive quantities!',
                'category': 'culture',
                'difficulty': 'beginner'
            },
            
            # Modern era
            {
                'title': 'Television Revolution',
                'content': 'Sumo was first televised in 1953 and became hugely popular on TV. Today, matches are broadcast worldwide and streamed online.',
                'category': 'modern',
                'difficulty': 'beginner'
            }
        ]
        
        for tip_data in initial_tips:
            self.add_tip(
                tip_data['title'],
                tip_data['content'],
                tip_data['category'],
                tip_data['difficulty']
            )
        
        print(f"Added {len(initial_tips)} initial sumo tips to database")
    
    def get_random_tip_by_category(self, category: str = None) -> Optional[Dict]:
        """Get a random tip, optionally from a specific category"""
        tips = self.get_all_tips(category)
        if not tips:
            return None
        
        # Weight selection towards less-used tips
        weighted_tips = []
        for tip in tips:
            # Tips with lower usage count get higher weight
            weight = max(1, 10 - tip['usage_count'])
            weighted_tips.extend([tip] * weight)
        
        return random.choice(weighted_tips) if weighted_tips else None