#!/usr/bin/env python3
"""
Test Pipeline Script

Runs the complete sumo news pipeline and saves the email output without sending it.
This allows you to review and refine the email content before enabling actual sending.
"""

import os
import sys
import time
from datetime import datetime

# Add the src directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from dotenv import load_dotenv
from scraper import SumoNewsScraper
from ai_processor import AIProcessor
from emailer import EmailSender

# Set up proper Unicode handling for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class TestPipeline:
    def __init__(self):
        load_dotenv()
        
        self.scraper = SumoNewsScraper()
        
        # Only initialize AI processor if API key is provided
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.ai_processor = AIProcessor(openai_key)
        else:
            self.ai_processor = None
            
        # Initialize email sender for content generation (but won't send)
        self.email_sender = EmailSender({
            'host': os.getenv('EMAIL_HOST'),
            'port': os.getenv('EMAIL_PORT'),
            'user': os.getenv('EMAIL_USER'),
            'pass': os.getenv('EMAIL_PASS'),
            'to': os.getenv('EMAIL_TO')
        })

    def run_pipeline_test(self):
        try:
            print('Sumo News Pipeline Test')
            print('======================')
            print('Running full pipeline and saving email content...\n')

            # Step 1: Get unprocessed articles from database
            print('Step 1: Getting articles from database...')
            news_items = self.scraper.get_unprocessed_articles(limit=10)
            
            if not news_items:
                print('No unprocessed news items found. Running scraper to get fresh content...')
                # Scrape fresh content for testing
                self.scraper.scrape_news(save_to_db=True)
                news_items = self.scraper.get_unprocessed_articles(limit=10)
            
            if not news_items:
                print('Still no articles found. Creating a test article...')
                news_items = [{
                    'id': 999,
                    'title': 'Test Sumo Tournament Results - Exciting Matches',
                    'url': 'https://example.com/test-tournament',
                    'content': 'Test tournament content with exciting sumo matches and results.',
                    'source': 'Test Source',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'raw_text': 'Test tournament featuring top sumo wrestlers'
                }]

            print(f'Found {len(news_items)} articles to process:')
            for i, item in enumerate(news_items):
                source_label = f"[{item.get('source', 'Unknown')}]"
                print(f'  {i + 1}. {source_label} {item["title"][:60]}...')

            # Step 2: Enhance with article content (optional)
            print('\nStep 2: Fetching article content...')
            for item in news_items:
                if not item.get('content'):
                    item['content'] = self.scraper.scrape_article_content(item['url'])
                    time.sleep(1)  # Rate limiting

            # Step 3: Process with AI (if available)
            if self.ai_processor:
                print('\nStep 3: Processing with AI...')
                processed_items = self.ai_processor.process_batch(news_items)
                
                print('AI summaries generated:')
                for i, item in enumerate(processed_items):
                    try:
                        print(f'  {i + 1}. {item["summary"]}')
                    except UnicodeEncodeError:
                        print(f'  {i + 1}. [Summary contains special characters]')

                # Create email digest metadata
                print('\nStep 4: Creating email digest metadata...')
                email_meta = self.ai_processor.create_email_digest(processed_items)
                print(f'Email subject: {email_meta["subject"]}')
                print(f'Email intro: {email_meta["intro"]}')
            else:
                print('\nStep 3: No OpenAI API key provided, using basic summaries...')
                processed_items = []
                for item in news_items:
                    processed_items.append({
                        **item,
                        'summary': f"Sumo News: {item['title'][:200]}",
                        'processed_at': time.time()
                    })
                    
                email_meta = {
                    'subject': 'Sumo Wrestling News Update - Test Pipeline',
                    'intro': 'Here are the latest updates from the world of sumo wrestling! (Test Mode)'
                }

            # Step 4: Generate email content (without sending)
            print('\nStep 5: Generating email content...')
            html_content = self.email_sender._generate_html_email(processed_items, email_meta)
            text_content = self.email_sender._generate_text_email(processed_items, email_meta)

            # Step 5: Save email files for review
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_dir = os.path.join(project_root, 'tests', 'output')
            os.makedirs(test_dir, exist_ok=True)

            # Save HTML version
            html_filename = f'test_email_{timestamp}.html'
            html_path = os.path.join(test_dir, html_filename)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Save text version
            text_filename = f'test_email_{timestamp}.txt'
            text_path = os.path.join(test_dir, text_filename)
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)

            # Save metadata JSON
            import json
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'subject': email_meta['subject'],
                'intro': email_meta['intro'],
                'article_count': len(processed_items),
                'articles': processed_items,
                'test_mode': True
            }
            
            json_filename = f'test_email_{timestamp}.json'
            json_path = os.path.join(test_dir, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            print(f'\nEmail content saved successfully!')
            print(f'HTML version: {html_path}')
            print(f'Text version: {text_path}')
            print(f'Metadata: {json_path}')
            
            # Show database stats
            stats = self.scraper.get_database_stats()
            print(f'\nDatabase Stats:')
            print(f'  Total articles: {stats["total_articles"]}')
            print(f'  Processed: {stats["processed_articles"]}')
            print(f'  Unprocessed: {stats["unprocessed_articles"]}')
            print(f'  Last 24h: {stats["articles_last_24h"]}')

            print(f'\nPipeline test completed successfully!')
            print(f'Review the generated files to refine your email content.')
            print(f'When ready, enable email sending in the main application.')
            
        except Exception as error:
            print(f'Pipeline test error: {error}')
            import traceback
            traceback.print_exc()


def main():
    """Run the test pipeline"""
    if len(sys.argv) > 1 and '--help' in sys.argv:
        print("""
Sumo News Pipeline Test

This script runs the complete news processing pipeline and saves
the email content without sending it. Use this to review and refine
the email format before enabling actual email delivery.

Usage:
  python tests/test_pipeline.py

Output files will be saved to tests/output/:
  - test_email_TIMESTAMP.html (HTML email version)
  - test_email_TIMESTAMP.txt (Text email version) 
  - test_email_TIMESTAMP.json (Metadata and article data)

Environment variables required:
  - OPENAI_API_KEY (optional, for AI summaries)
  - EMAIL_TO (for recipient info in email)
""")
        return

    pipeline = TestPipeline()
    pipeline.run_pipeline_test()


if __name__ == '__main__':
    main()