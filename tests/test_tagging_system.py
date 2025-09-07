#!/usr/bin/env python3
"""
Test Tagging System

Tests the complete tagging functionality including AI generation, 
database storage, and tag management.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from database import NewsDatabase
from ai_processor import AIProcessor
from tag_manager import TagManager
from similarity_analyzer import SimilarityAnalyzer
from dotenv import load_dotenv
import time


def main():
    print("Tagging System Test")
    print("=" * 30)
    
    load_dotenv()
    
    # Initialize components
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("ERROR: No OpenAI API key found")
        return
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sumo_news.db')
    db = NewsDatabase(db_path)
    ai_processor = AIProcessor(openai_key)
    tag_manager = TagManager(db)
    analyzer = SimilarityAnalyzer(db, ai_processor)
    
    # Test 1: Create some test tags manually
    print("\n1. Creating test tags...")
    test_tags = [
        ('yokozuna', 'rank', 'Grand champion rank', '#FFD700'),
        ('tournament', 'event', 'Sumo tournament', '#FF6B6B'),
        ('promotion', 'event', 'Wrestler promotion', '#4ECDC4'),
        ('tokyo', 'location', 'Tokyo location', '#45B7D1'),
        ('september-2025', 'date', 'September 2025', '#96CEB4')
    ]
    
    for name, category, description, color in test_tags:
        tag_id = tag_manager.create_tag(name, category, description, color)
        if tag_id:
            print(f"Created tag: {name} (ID: {tag_id})")
    
    # Test 2: Test AI tag generation
    print("\n2. Testing AI tag generation...")
    test_article = {
        'title': 'Onosato Promoted to Yokozuna After Historic Tournament Victory',
        'content': '''Onosato from Nishonoseki stable has been promoted to yokozuna 
                     following his dominant performance in the September 2025 basho in Tokyo. 
                     The 25-year-old wrestler achieved a perfect 15-0 record, defeating 
                     ozeki Terunofuji in the final match. This promotion makes him the 
                     75th yokozuna in sumo history. The Japan Sumo Association announced 
                     the promotion during a ceremony at the Kokugikan.''',
        'url': 'https://example.com/test',
        'source': 'Test Source'
    }
    
    try:
        tags, scores = ai_processor.generate_tags_for_article(
            test_article['title'],
            test_article['content'],
            ['Onosato', 'Terunofuji', 'Nishonoseki']
        )
        
        print(f"Generated {len(tags)} tags:")
        for i, tag in enumerate(tags):
            score = scores[i] if i < len(scores) else 'N/A'
            print(f"  - {tag} (confidence: {score})")
            
    except Exception as e:
        print(f"Error in AI tag generation: {e}")
        tags, scores = [], []
    
    # Test 3: Test tag categorization
    print("\n3. Testing automatic tag categorization...")
    test_tag_names = [
        'september-basho', 'yokozuna-promotion', 'tokyo-tournament', 
        'ozeki', 'interview-special', 'jsa-announcement'
    ]
    
    for tag_name in test_tag_names:
        category = tag_manager.auto_categorize_tag(tag_name)
        print(f"  '{tag_name}' -> category: {category}")
    
    # Test 4: Add tags to an existing article
    print("\n4. Testing tag assignment to articles...")
    
    # Get a real article from database
    articles = db.get_recent_articles(days=30, limit=3)
    if articles:
        test_article_db = articles[0]
        article_id = test_article_db['id']
        
        print(f"Testing with article ID {article_id}: {test_article_db['title'][:50]}...")
        
        # Add some test tags
        test_tags_to_add = ['tournament', 'banzuke', '2025', 'jsa']
        added_count = tag_manager.add_tags_to_article(article_id, test_tags_to_add)
        print(f"Added {added_count} tags to article {article_id}")
        
        # Retrieve and display tags
        article_tags = tag_manager.get_article_tags(article_id)
        print(f"Article now has {len(article_tags)} tags:")
        for tag_info in article_tags:
            print(f"  - {tag_info['name']} ({tag_info['category']}, confidence: {tag_info['confidence_score']})")
    
    # Test 5: Search articles by tags
    print("\n5. Testing tag-based search...")
    
    # Search for articles with specific tags
    tournament_articles = tag_manager.get_articles_by_tag('tournament', limit=5)
    print(f"Found {len(tournament_articles)} articles with 'tournament' tag")
    
    # Search by category
    rank_articles = tag_manager.get_articles_by_category('rank', limit=5)
    print(f"Found {len(rank_articles)} articles with 'rank' category tags")
    
    # Test 6: Tag statistics
    print("\n6. Tag statistics...")
    stats = tag_manager.get_tag_statistics()
    print(f"Total tags: {stats['total_tags']}")
    print(f"Articles with tags: {stats['articles_with_tags']}")
    print(f"Tags by category: {stats['tags_by_category']}")
    
    if stats['most_used_tags']:
        print("Most used tags:")
        for tag_info in stats['most_used_tags'][:5]:
            print(f"  - {tag_info['name']} ({tag_info['category']}): {tag_info['count']} uses")
    
    # Test 7: Test complete article processing with tags
    print("\n7. Testing complete article processing with tagging...")
    
    if tags:  # If we have generated tags from step 2
        print("Processing test article with full tagging pipeline...")
        
        try:
            # This would normally be done by the scraper
            result = analyzer.process_new_article(test_article, similarity_threshold=0.8)
            
            if result['article_id']:
                print(f"Article processed successfully with ID: {result['article_id']}")
                print(f"Tags generated: {result.get('tags', [])}")
                
                # Get the tags that were actually saved
                saved_tags = tag_manager.get_article_tags(result['article_id'])
                print(f"Tags saved to database: {len(saved_tags)}")
                for tag_info in saved_tags:
                    print(f"  - {tag_info['name']} ({tag_info['category']})")
                    
        except Exception as e:
            print(f"Error in complete processing: {e}")
    
    print("\n>>> Tagging system test completed!")


if __name__ == '__main__':
    main()