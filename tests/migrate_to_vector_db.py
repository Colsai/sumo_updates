#!/usr/bin/env python3
"""
Vector Database Migration Script

Migrates existing SQLite database to support vector embeddings and relationships.
This script can be run safely multiple times.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from database import NewsDatabase
from ai_processor import AIProcessor
from similarity_analyzer import SimilarityAnalyzer
from dotenv import load_dotenv


def migrate_database_schema(db_path: str):
    """Add new columns to existing database if they don't exist"""
    print("=== Database Schema Migration ===")
    
    # Initialize database (this will create new tables and columns)
    db = NewsDatabase(db_path)
    print(">>> Database schema updated with vector support")
    
    return db


def process_existing_articles(db: NewsDatabase, ai_processor: AIProcessor, batch_size: int = 5):
    """Process existing articles to generate embeddings and relationships"""
    print("\n=== Processing Existing Articles ===")
    
    analyzer = SimilarityAnalyzer(db, ai_processor)
    
    # Get articles without embeddings
    articles = db.get_articles_without_embeddings(limit=batch_size)
    
    if not articles:
        print(">>> All articles already have embeddings")
        return
    
    print(f"Found {len(articles)} articles without embeddings")
    
    results = analyzer.batch_process_existing_articles(limit=batch_size)
    
    print(f">>> Migration results:")
    print(f"  - Processed: {results['processed']}")
    print(f"  - Errors: {results['errors']}")
    print(f"  - New relationships: {results['new_relationships']}")


def test_vector_functionality(db: NewsDatabase, ai_processor: AIProcessor):
    """Test that vector functionality is working"""
    print("\n=== Testing Vector Functionality ===")
    
    try:
        # Test embedding generation
        test_text = "Sumo wrestling tournament results"
        embedding = ai_processor.generate_single_embedding(test_text)
        
        if embedding:
            print(f">>> Embedding generation working (dimension: {len(embedding)})")
            
            # Test similarity search (even if no results)
            similar = db.find_similar_articles(embedding, similarity_threshold=0.5, limit=5)
            print(f">>> Similarity search working (found {len(similar)} similar articles)")
        else:
            print("ERROR: Embedding generation failed")
            
        # Test entity extraction
        entities, topics = ai_processor.extract_entities_and_topics(
            "Yokozuna Terunofuji wins the tournament", 
            "Championship Results"
        )
        print(f">>> Entity extraction working (entities: {len(entities)}, topics: {len(topics)})")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Vector functionality test failed: {e}")
        return False


def get_database_stats(db: NewsDatabase):
    """Display current database statistics"""
    print("\n=== Database Statistics ===")
    
    stats = db.get_stats()
    print(f"Total articles: {stats['total_articles']}")
    print(f"Processed articles: {stats['processed_articles']}")
    print(f"Articles with embeddings: ", end="")
    
    # Count articles with embeddings
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM news_articles WHERE content_embedding IS NOT NULL')
            with_embeddings = cursor.fetchone()[0]
            print(f"{with_embeddings}")
            
            # Count relationships
            cursor.execute('SELECT COUNT(*) FROM article_relationships')
            relationships = cursor.fetchone()[0]
            print(f"Article relationships: {relationships}")
            
    except Exception as e:
        print(f"Error getting embedding stats: {e}")


def main():
    print("Sumo News Vector Database Migration")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Check for OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        print("Please set up your .env file with OpenAI API key for full functionality")
        
        # Still run schema migration without AI features
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sumo_news.db')
        migrate_database_schema(db_path)
        print(">>> Schema migration completed (without AI features)")
        return
    
    # Set up database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sumo_news.db')
    
    print(f"Database path: {db_path}")
    
    try:
        # Step 1: Migrate database schema
        db = migrate_database_schema(db_path)
        
        # Step 2: Initialize AI processor
        print("\nInitializing AI processor...")
        ai_processor = AIProcessor(openai_key)
        
        # Step 3: Test vector functionality
        if test_vector_functionality(db, ai_processor):
            # Step 4: Process existing articles (small batch for testing)
            print("\nProcessing sample of existing articles...")
            process_existing_articles(db, ai_processor, batch_size=3)
        
        # Step 5: Show final stats
        get_database_stats(db)
        
        print("\n>>> Migration completed successfully!")
        print("\nTo process all existing articles, run:")
        print("python tests/migrate_to_vector_db.py --full")
        
    except ImportError as e:
        print(f"ERROR Import error: {e}")
        print("Make sure sqlite-vec is installed: pip install sqlite-vec")
        
    except Exception as e:
        print(f"ERROR Migration error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Check if full migration requested
    if '--full' in sys.argv:
        load_dotenv()
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sumo_news.db')
        db = NewsDatabase(db_path)
        ai_processor = AIProcessor(os.getenv('OPENAI_API_KEY'))
        
        print("Running FULL migration of all existing articles...")
        analyzer = SimilarityAnalyzer(db, ai_processor)
        results = analyzer.batch_process_existing_articles()  # No limit
        
        print(f"Full migration results:")
        print(f"  - Processed: {results['processed']}")
        print(f"  - Errors: {results['errors']}")
        print(f"  - New relationships: {results['new_relationships']}")
    else:
        main()