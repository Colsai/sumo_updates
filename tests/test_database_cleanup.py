#!/usr/bin/env python3
"""
Test Database Cleanup and Optimization

Tests automatic duplicate removal and database optimization.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from database import NewsDatabase


def main():
    print("Database Cleanup and Optimization Test")
    print("=" * 45)
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sumo_news.db')
    db = NewsDatabase(db_path)
    
    # Step 1: Analyze current database state
    print("\n1. Analyzing current database state...")
    analysis = db.get_duplicate_analysis()
    
    print(f"   Total articles: {analysis['total_articles']}")
    print(f"   URL duplicates: {analysis['url_duplicates']}")
    print(f"   Semantic duplicates: {analysis['semantic_duplicates']}")
    
    if analysis['similar_titles']:
        print(f"   Similar titles found:")
        for item in analysis['similar_titles'][:5]:
            print(f"   - '{item['title'][:60]}...' ({item['count']} times)")
    
    # Step 2: Test duplicate removal (dry run analysis)
    print(f"\n2. Testing duplicate removal...")
    
    if analysis['url_duplicates'] > 0 or analysis['semantic_duplicates'] > 0:
        print("   Removing duplicates...")
        results = db.remove_duplicate_articles()
        
        print(f"   Results:")
        print(f"   - URL duplicates removed: {results['url_duplicates_removed']}")
        print(f"   - Semantic duplicates removed: {results['semantic_duplicates_removed']}")
        print(f"   - Total removed: {results['total_removed']}")
        print(f"   - Errors: {results['errors']}")
    else:
        print("   No duplicates found to remove")
        results = {'total_removed': 0}
    
    # Step 3: Full database optimization
    print(f"\n3. Database optimization...")
    
    if results['total_removed'] > 0:
        print("   Running VACUUM to reclaim space...")
        try:
            with db._get_connection() as conn:
                conn.execute('VACUUM')
                print("   Database vacuumed successfully")
        except Exception as e:
            print(f"   Error vacuuming database: {e}")
    else:
        print("   No optimization needed")
    
    # Step 4: Final analysis
    print(f"\n4. Final database state...")
    final_analysis = db.get_duplicate_analysis()
    
    print(f"   Total articles: {final_analysis['total_articles']}")
    print(f"   URL duplicates: {final_analysis['url_duplicates']}")
    print(f"   Semantic duplicates: {final_analysis['semantic_duplicates']}")
    
    space_saved = analysis['total_articles'] - final_analysis['total_articles']
    if space_saved > 0:
        print(f"   Space saved: {space_saved} articles removed")
    
    print("\n>>> Database cleanup test completed!")


if __name__ == '__main__':
    main()