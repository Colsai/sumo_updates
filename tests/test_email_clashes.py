#!/usr/bin/env python3
"""
Test Email Clash Detection

Tests the email clash checker to identify duplicate content in previous emails.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from email_clash_checker import EmailClashChecker
from ai_processor import AIProcessor
from database import NewsDatabase
from dotenv import load_dotenv
import json


def main():
    print("Email Clash Detection Test")
    print("=" * 40)
    
    load_dotenv()
    
    # Initialize components
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("WARNING: No OpenAI API key found. Semantic analysis disabled.")
        ai_processor = None
    else:
        ai_processor = AIProcessor(openai_key)
    
    archives_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'archives')
    clash_checker = EmailClashChecker(archives_dir, ai_processor)
    
    # Test 1: Get clash report
    print("\n1. Analyzing previous email archives...")
    report = clash_checker.get_clash_report(days_back=30)
    
    if 'message' in report:
        print(f"   {report['message']}")
    else:
        print(f"   Archives analyzed: {report['archives_analyzed']}")
        print(f"   Date range: {report['date_range']}")
        print(f"   Overlapping email pairs: {report['overlapping_pairs']}")
        
        if report['overlaps']:
            print("\n   Detected overlaps:")
            for overlap in report['overlaps']:
                print(f"   - Email 1: {overlap['email1']['file']}")
                print(f"     Email 2: {overlap['email2']['file']}")
                print(f"     Common articles: {overlap['common_count']} (IDs: {overlap['common_article_ids']})")
                print()
    
    # Test 2: Get some articles from database to test filtering
    print("\n2. Testing article filtering...")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sumo_news.db')
    db = NewsDatabase(db_path)
    
    # Get some unprocessed articles
    test_articles = db.get_unprocessed_articles(limit=15)
    
    if test_articles:
        print(f"   Testing with {len(test_articles)} articles...")
        
        # Filter articles for email
        filter_result = clash_checker.filter_articles_for_email(test_articles, check_days=7)
        
        print(f"\n   Filter Results:")
        summary = filter_result['analysis_summary']
        print(f"   - Original articles: {summary['original_count']}")
        print(f"   - Exact duplicates: {summary['exact_duplicates']}")
        print(f"   - Similar articles: {summary['similar_articles']}")
        print(f"   - Approved articles: {summary['approved_count']}")
        print(f"   - Archives checked: {summary['archives_checked']}")
        
        if filter_result['rejected_duplicates']:
            print(f"\n   Rejected duplicates:")
            for article in filter_result['rejected_duplicates']:
                print(f"   - [{article.get('id')}] {article.get('title', 'Unknown')}")
        
        if filter_result['rejected_similar']:
            print(f"\n   Rejected similar articles:")
            for item in filter_result['rejected_similar']:
                article = item['article']
                print(f"   - [{article.get('id')}] {article.get('title', 'Unknown')[:60]}...")
                print(f"     Reason: {item.get('reason', 'No reason given')}")
    else:
        print("   No articles available for testing")
    
    print("\n>>> Email clash detection test completed!")


if __name__ == '__main__':
    main()