#!/usr/bin/env python3
"""
Tag Management Tool

Command-line utility for managing tags in the sumo news database.
"""

import os
import sys
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from database import NewsDatabase
from tag_manager import TagManager
from ai_processor import AIProcessor
from dotenv import load_dotenv
import sqlite3


def list_tags(tag_manager: TagManager, category: str = None):
    """List all tags or tags in a specific category"""
    tags = tag_manager.get_all_tags(category, limit=100)
    
    if category:
        print(f"Tags in category '{category}':")
    else:
        print("All tags:")
    
    if not tags:
        print("No tags found.")
        return
    
    # Group by category
    by_category = {}
    for tag in tags:
        cat = tag['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(tag)
    
    for category, category_tags in sorted(by_category.items()):
        print(f"\n{category.upper()}:")
        for tag in category_tags:
            usage = f"({tag['usage_count']} uses)" if tag['usage_count'] > 0 else "(unused)"
            desc = f" - {tag['description']}" if tag.get('description') else ""
            print(f"  {tag['name']} {usage}{desc}")


def show_statistics(tag_manager: TagManager):
    """Show tag usage statistics"""
    stats = tag_manager.get_tag_statistics()
    
    print("Tag Statistics:")
    print(f"Total tags: {stats['total_tags']}")
    print(f"Articles with tags: {stats['articles_with_tags']}")
    
    print(f"\nTags by category:")
    for category, count in stats['tags_by_category'].items():
        print(f"  {category}: {count}")
    
    print(f"\nMost used tags:")
    for tag_info in stats['most_used_tags'][:10]:
        print(f"  {tag_info['name']} ({tag_info['category']}): {tag_info['count']} uses")


def search_articles(tag_manager: TagManager, tags: list, match_type: str = 'any'):
    """Search articles by tags"""
    articles = tag_manager.search_articles_by_tags(tags, match_type, limit=20)
    
    print(f"Articles with {match_type.upper()} of tags {tags}:")
    if not articles:
        print("No articles found.")
        return
    
    for article in articles:
        article_tags = tag_manager.get_article_tags(article['id'])
        tag_names = [tag['name'] for tag in article_tags]
        print(f"[{article['id']}] {article['title'][:60]}...")
        print(f"  Tags: {', '.join(tag_names)}")
        print(f"  Source: {article.get('source', 'Unknown')}")
        print(f"  Date: {article.get('scraped_at', 'Unknown')}")
        print()


def tag_article(tag_manager: TagManager, article_id: int, tags: list):
    """Add tags to a specific article"""
    added = tag_manager.add_tags_to_article(article_id, tags, created_by='manual')
    print(f"Added {added} tags to article {article_id}")


def show_article_tags(tag_manager: TagManager, article_id: int, db: NewsDatabase):
    """Show all tags for a specific article"""
    # Get article info
    with db._get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM news_articles WHERE id = ?', (article_id,))
        article = cursor.fetchone()
        
        if not article:
            print(f"Article {article_id} not found.")
            return
    
    print(f"Article {article_id}: {article['title']}")
    print(f"Source: {article['source']}")
    print(f"Date: {article['scraped_at']}")
    
    tags = tag_manager.get_article_tags(article_id)
    if tags:
        print(f"\nTags ({len(tags)}):")
        for tag in tags:
            print(f"  {tag['name']} ({tag['category']}, confidence: {tag['confidence_score']:.2f})")
    else:
        print("\nNo tags assigned.")


def bulk_tag_articles(tag_manager: TagManager, ai_processor: AIProcessor, db: NewsDatabase, limit: int = 10):
    """Add AI-generated tags to articles that don't have tags yet"""
    print(f"Adding AI-generated tags to up to {limit} articles...")
    
    # Get articles without tags
    with db._get_connection() as conn:
        conn.row_factory = db.sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT na.* FROM news_articles na
            LEFT JOIN article_tags at ON na.id = at.article_id
            WHERE at.article_id IS NULL
            ORDER BY na.scraped_at DESC
            LIMIT ?
        ''', (limit,))
        
        articles = [dict(row) for row in cursor.fetchall()]
    
    if not articles:
        print("No articles without tags found.")
        return
    
    print(f"Processing {len(articles)} articles...")
    
    for i, article in enumerate(articles):
        print(f"\n{i+1}/{len(articles)}: {article['title'][:50]}...")
        
        try:
            # Generate tags using AI
            tags, scores = ai_processor.generate_tags_for_article(
                article['title'],
                article.get('content', ''),
                article.get('entities', '').split(',') if article.get('entities') else []
            )
            
            if tags:
                added = tag_manager.add_tags_to_article(
                    article['id'], 
                    tags, 
                    scores,
                    'ai-bulk'
                )
                print(f"  Added {added} tags: {tags[:3]}..." if len(tags) > 3 else f"  Added {added} tags: {tags}")
            else:
                print("  No tags generated")
                
        except Exception as e:
            print(f"  Error: {e}")
        
        # Rate limiting
        import time
        time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description='Tag Management Tool')
    parser.add_argument('command', choices=['list', 'stats', 'search', 'tag', 'show', 'bulk-tag'],
                       help='Command to execute')
    parser.add_argument('--category', help='Tag category filter')
    parser.add_argument('--tags', nargs='+', help='List of tags')
    parser.add_argument('--article-id', type=int, help='Article ID')
    parser.add_argument('--match-type', choices=['any', 'all'], default='any',
                       help='Match any or all tags (for search)')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of results')
    
    args = parser.parse_args()
    
    # Initialize
    load_dotenv()
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sumo_news.db')
    db = NewsDatabase(db_path)
    tag_manager = TagManager(db)
    
    if args.command == 'list':
        list_tags(tag_manager, args.category)
        
    elif args.command == 'stats':
        show_statistics(tag_manager)
        
    elif args.command == 'search':
        if not args.tags:
            print("Error: --tags required for search")
            return
        search_articles(tag_manager, args.tags, args.match_type)
        
    elif args.command == 'tag':
        if not args.article_id or not args.tags:
            print("Error: --article-id and --tags required")
            return
        tag_article(tag_manager, args.article_id, args.tags)
        
    elif args.command == 'show':
        if not args.article_id:
            print("Error: --article-id required")
            return
        show_article_tags(tag_manager, args.article_id, db)
        
    elif args.command == 'bulk-tag':
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("Error: OPENAI_API_KEY required for bulk tagging")
            return
        
        ai_processor = AIProcessor(openai_key)
        bulk_tag_articles(tag_manager, ai_processor, db, args.limit)


if __name__ == '__main__':
    main()