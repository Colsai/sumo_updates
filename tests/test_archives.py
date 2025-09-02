#!/usr/bin/env python3
"""
Test script to verify email archiving functionality
"""

import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from emailer import EmailSender
from database import NewsDatabase

def test_archiving():
    print("Testing Email Archiving Functionality")
    print("=" * 50)
    
    # Create sample email content
    sample_summaries = [
        {
            'source': 'Japan Sumo Association',
            'title': 'Tournament Results Announced',
            'summary': 'Terunofuji wins championship with impressive 14-1 record, defeating all challengers.',
            'url': 'https://www.sumo.or.jp/test1',
            'date': '2025-09-02'
        },
        {
            'source': 'Japan Times',
            'title': 'Rising Sumo Stars',
            'summary': 'Young wrestlers show promise in upcoming tournament rankings.',
            'url': 'https://www.japantimes.co.jp/test2',
            'date': '2025-09-01'
        }
    ]
    
    sample_email_meta = {
        'subject': 'Test Sumo News Digest - Archive Test',
        'intro': 'This is a test email to verify the archiving functionality works correctly.',
    }
    
    # Mock email config (we won't actually send)
    config = {
        'host': 'test.com',
        'port': '587',
        'user': 'test@test.com',
        'pass': 'test',
        'to': 'recipient@test.com'
    }
    
    try:
        # Create emailer instance
        emailer = EmailSender(config)
        
        # Generate email content
        html_content = emailer._generate_html_email(sample_summaries, sample_email_meta)
        text_content = emailer._generate_text_email(sample_summaries, sample_email_meta)
        
        # Save to archives (this is the main function we want to test)
        emailer._save_email_archive(sample_summaries, sample_email_meta, html_content, text_content)
        
        print("Archive saved successfully!")
        print("\nNow testing archive viewing...")
        
        # Test archive viewing
        os.system('python view_archives.py')
        
        return True
        
    except Exception as e:
        print(f"Archive test failed: {e}")
        return False

if __name__ == "__main__":
    test_archiving()