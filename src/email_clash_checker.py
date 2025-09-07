"""
Email Clash Checker

Analyzes previous emails to detect content overlaps and prevent duplicate articles
in new email digests.
"""

import os
import json
import glob
from typing import List, Dict, Set, Tuple
from datetime import datetime, timedelta
from ai_processor import AIProcessor


class EmailClashChecker:
    def __init__(self, archives_dir: str = 'archives', ai_processor: AIProcessor = None):
        self.archives_dir = archives_dir
        self.ai_processor = ai_processor
    
    def get_recent_email_archives(self, days_back: int = 30) -> List[Dict]:
        """Get email archives from the last N days"""
        archives = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        if not os.path.exists(self.archives_dir):
            return archives
        
        # Find all JSON email archives
        pattern = os.path.join(self.archives_dir, "email_*.json")
        archive_files = glob.glob(pattern)
        
        for file_path in archive_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    archive = json.load(f)
                    
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(archive['timestamp'])
                    if timestamp >= cutoff_date:
                        archive['file_path'] = file_path
                        archives.append(archive)
                        
            except Exception as e:
                print(f"Error reading archive {file_path}: {e}")
        
        # Sort by timestamp (newest first)
        archives.sort(key=lambda x: x['timestamp'], reverse=True)
        return archives
    
    def extract_article_ids_from_archives(self, archives: List[Dict]) -> Set[int]:
        """Extract all article IDs that have been sent in recent emails"""
        sent_ids = set()
        
        for archive in archives:
            articles = archive.get('articles', [])
            for article in articles:
                if 'id' in article:
                    sent_ids.add(article['id'])
        
        return sent_ids
    
    def check_exact_duplicates(self, new_articles: List[Dict], 
                             recent_archives: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Check for exact duplicate articles by ID"""
        sent_ids = self.extract_article_ids_from_archives(recent_archives)
        
        new_articles_filtered = []
        duplicate_articles = []
        
        for article in new_articles:
            article_id = article.get('id')
            if article_id and article_id in sent_ids:
                duplicate_articles.append(article)
            else:
                new_articles_filtered.append(article)
        
        return new_articles_filtered, duplicate_articles
    
    def analyze_content_similarity(self, new_articles: List[Dict], 
                                 recent_archives: List[Dict]) -> List[Dict]:
        """Use AI to analyze semantic similarity between new and previous content"""
        if not self.ai_processor or not recent_archives:
            return []
        
        # Extract previous article summaries and titles
        previous_content = []
        for archive in recent_archives[:3]:  # Only check last 3 emails
            for article in archive.get('articles', [])[:5]:  # Top 5 articles per email
                content = f"{article.get('title', '')} - {article.get('summary', '')}"
                previous_content.append({
                    'content': content,
                    'title': article.get('title', ''),
                    'timestamp': archive.get('timestamp', ''),
                    'id': article.get('id')
                })
        
        if not previous_content:
            return []
        
        similar_articles = []
        
        for new_article in new_articles:
            try:
                new_content = f"{new_article.get('title', '')} - {new_article.get('summary', '')}"
                
                # Create prompt for similarity analysis
                prev_summaries = '\n'.join([
                    f"• {item['title']} ({item.get('timestamp', 'Unknown date')})"
                    for item in previous_content[:10]
                ])
                
                prompt = f"""Compare this new sumo wrestling article with previous articles:

NEW ARTICLE: {new_content[:300]}

PREVIOUS ARTICLES:
{prev_summaries}

Is this new article similar to any previous ones? Consider:
1. Same event/tournament being covered
2. Same wrestler promotions/news
3. Similar content themes
4. Updates vs original stories

Respond with JSON:
{{
  "is_similar": true/false,
  "similarity_score": 0.0-1.0,
  "similar_to": "title of most similar article or null",
  "reason": "brief explanation"
}}"""

                if hasattr(self.ai_processor, 'openai'):
                    response = self.ai_processor.openai.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[{'role': 'user', 'content': prompt}],
                        max_tokens=150,
                        temperature=0.3
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    try:
                        result = json.loads(result_text)
                        if result.get('is_similar', False) and result.get('similarity_score', 0) > 0.7:
                            similar_articles.append({
                                'article': new_article,
                                'similarity_score': result.get('similarity_score'),
                                'similar_to': result.get('similar_to'),
                                'reason': result.get('reason', '')
                            })
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                print(f"Error analyzing similarity for {new_article.get('title', 'Unknown')}: {e}")
        
        return similar_articles
    
    def filter_articles_for_email(self, articles: List[Dict], 
                                check_days: int = 7) -> Dict:
        """Filter articles to avoid content clashes with recent emails"""
        result = {
            'approved_articles': [],
            'rejected_duplicates': [],
            'rejected_similar': [],
            'analysis_summary': {}
        }
        
        # Get recent email archives
        recent_archives = self.get_recent_email_archives(check_days)
        
        print(f"Checking for clashes with {len(recent_archives)} recent emails...")
        
        # Step 1: Remove exact duplicates
        filtered_articles, exact_dupes = self.check_exact_duplicates(articles, recent_archives)
        result['rejected_duplicates'] = exact_dupes
        
        if exact_dupes:
            print(f"  >> Found {len(exact_dupes)} exact duplicates (by ID)")
        
        # Step 2: Analyze semantic similarity
        if self.ai_processor and filtered_articles:
            similar_articles = self.analyze_content_similarity(filtered_articles, recent_archives)
            
            # Remove semantically similar articles
            similar_ids = {item['article'].get('id') for item in similar_articles}
            truly_new_articles = [
                article for article in filtered_articles 
                if article.get('id') not in similar_ids
            ]
            
            result['approved_articles'] = truly_new_articles
            result['rejected_similar'] = similar_articles
            
            if similar_articles:
                print(f"  >> Found {len(similar_articles)} semantically similar articles")
                for item in similar_articles:
                    print(f"    - {item['article'].get('title', 'Unknown')[:50]}... "
                          f"(similar to: {item.get('similar_to', 'Unknown')})")
        else:
            result['approved_articles'] = filtered_articles
        
        result['analysis_summary'] = {
            'original_count': len(articles),
            'exact_duplicates': len(exact_dupes),
            'similar_articles': len(result['rejected_similar']),
            'approved_count': len(result['approved_articles']),
            'archives_checked': len(recent_archives)
        }
        
        print(f"  >> Final result: {len(result['approved_articles'])}/{len(articles)} articles approved")
        
        return result
    
    def get_clash_report(self, days_back: int = 30) -> Dict:
        """Generate a report of potential content overlaps in recent emails"""
        archives = self.get_recent_email_archives(days_back)
        
        if len(archives) < 2:
            return {'message': 'Not enough email archives to analyze'}
        
        # Check for article ID overlaps between emails
        overlaps = []
        
        for i, archive1 in enumerate(archives):
            for j, archive2 in enumerate(archives[i+1:], i+1):
                ids1 = {article.get('id') for article in archive1.get('articles', [])}
                ids2 = {article.get('id') for article in archive2.get('articles', [])}
                
                common_ids = ids1.intersection(ids2)
                if common_ids:
                    overlaps.append({
                        'email1': {
                            'date': archive1.get('timestamp', ''),
                            'subject': archive1.get('subject', ''),
                            'file': os.path.basename(archive1.get('file_path', ''))
                        },
                        'email2': {
                            'date': archive2.get('timestamp', ''),
                            'subject': archive2.get('subject', ''), 
                            'file': os.path.basename(archive2.get('file_path', ''))
                        },
                        'common_article_ids': list(common_ids),
                        'common_count': len(common_ids)
                    })
        
        return {
            'archives_analyzed': len(archives),
            'date_range': f"{archives[-1].get('timestamp', '')} to {archives[0].get('timestamp', '')}",
            'overlapping_pairs': len(overlaps),
            'overlaps': overlaps
        }