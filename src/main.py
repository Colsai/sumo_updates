import os
import sys
import time
from dotenv import load_dotenv
from scraper import SumoNewsScraper
from ai_processor import AIProcessor
from emailer import EmailSender
from email_clash_checker import EmailClashChecker

# Set up proper Unicode handling for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class SumoNewsApp:
    def __init__(self):
        load_dotenv()
        
        # Only initialize AI processor if API key is provided
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.ai_processor = AIProcessor(openai_key)
        else:
            self.ai_processor = None
            
        # Initialize scraper with AI processor for vector capabilities
        self.scraper = SumoNewsScraper(ai_processor=self.ai_processor)
        
        # Initialize email clash checker
        archives_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'archives')
        self.clash_checker = EmailClashChecker(archives_dir, self.ai_processor)
            
        self.email_sender = EmailSender({
            'host': os.getenv('EMAIL_HOST'),
            'port': os.getenv('EMAIL_PORT'),
            'user': os.getenv('EMAIL_USER'),
            'pass': os.getenv('EMAIL_PASS'),
            'to': os.getenv('EMAIL_TO')
        })

    def run(self, dry_run=False):
        try:
            print('''
    Sumo News Emailer
         ___
        ( o.o )
         \\_/
    ''')
            print('Starting Sumo News Digest Generation...')
            print('=' * 50)

            # Step 1: Scrape news and save to database
            print('Scraping news from multiple sources...')
            self.scraper.scrape_news(save_to_db=True)

            # Step 2: Get unprocessed articles from database
            print('Getting unprocessed articles from database...')
            raw_news_items = self.scraper.get_unprocessed_articles(limit=20)
            
            if not raw_news_items:
                print('No unprocessed news items found. Exiting.')
                return

            print(f'Found {len(raw_news_items)} unprocessed news items')
            
            # Step 2a: Filter articles to avoid email clashes
            print('\nFiltering articles to avoid email content clashes...')
            filter_result = self.clash_checker.filter_articles_for_email(raw_news_items, check_days=14)
            news_items = filter_result['approved_articles'][:10]  # Limit to top 10 approved
            
            if not news_items:
                print('All articles filtered out due to recent duplicates. No new content to send.')
                return
            
            print(f'After filtering: {len(news_items)} articles approved for email:')
            for i, item in enumerate(news_items):
                source_label = f"[{item.get('source', 'Unknown')}]"
                print(f'  {i + 1}. {source_label} {item["title"][:60]}...')

            # Step 2b: Enhance with article content (optional)
            print('\nFetching article content...')
            for item in news_items:
                if not item.get('content'):
                    item['content'] = self.scraper.scrape_article_content(item['url'])
                    time.sleep(1)  # Rate limiting

            # Step 3: Process with AI (if available)
            if self.ai_processor:
                print('\nProcessing with AI...')
                processed_items = self.ai_processor.process_batch(news_items)
                
                print('AI summaries generated:')
                for i, item in enumerate(processed_items):
                    try:
                        print(f'  {i + 1}. {item["summary"]}')
                    except UnicodeEncodeError:
                        print(f'  {i + 1}. [Summary contains special characters]')

                # Step 4: Create email digest
                print('\nCreating email digest...')
                email_meta = self.ai_processor.create_email_digest(processed_items)
                print(f'Email subject: {email_meta["subject"]}')
                print(f'Email intro: {email_meta["intro"]}')
            else:
                print('\nNo OpenAI API key provided, using basic summaries...')
                processed_items = []
                for item in news_items:
                    processed_items.append({
                        **item,
                        'summary': f"Sumo: {item['title'][:250]}",
                        'processed_at': time.time()
                    })
                    
                email_meta = {
                    'subject': 'Sumo Wrestling News Update',
                    'intro': 'Here are the latest updates from the world of sumo wrestling!'
                }

            # Step 5: Send email
            if dry_run:
                print('\nDRY RUN: Generating email content without sending...')
            else:
                print('\nSending email...')
            result = self.email_sender.send_news_digest(processed_items, email_meta, dry_run=dry_run)
            
            if result['success']:
                if dry_run:
                    print('Dry run completed successfully!')
                    print(f'Simulated Message ID: {result.get("message_id", "N/A")}')
                    print('\nEmail content has been generated and archived.')
                    print('Review the archived email in the archives/ folder.')
                    print('When ready, run without --dry-run to send actual emails.')
                else:
                    print('Email sent successfully!')
                    print(f'Message ID: {result.get("message_id", "N/A")}')
                    print('\nNote: Recipients can unsubscribe by replying with "UNSUBSCRIBE"')
                    print('or by contacting the sender directly.')
                
                # Mark articles as processed in database (only if not dry run)
                if not dry_run:
                    summaries = [item.get('summary', '') for item in processed_items]
                    self.scraper.mark_articles_processed(processed_items, summaries)
                    print('Articles marked as processed in database.')
                else:
                    print('Dry run: Articles not marked as processed (can be reused for testing).')
                
            else:
                print(f'Failed to send email: {result["error"]}')

            # Show database stats
            stats = self.scraper.get_database_stats()
            print(f'\nDatabase Stats:')
            print(f'  Total articles: {stats["total_articles"]}')
            print(f'  Processed: {stats["processed_articles"]}')
            print(f'  Unprocessed: {stats["unprocessed_articles"]}')
            print(f'  Last 24h: {stats["articles_last_24h"]}')

            print('''
    Digest Complete! \\o/
    
    Sumo News Digest completed successfully!
    ''')
            
        except Exception as error:
            print(f'Application error: {error}')
            import traceback
            traceback.print_exc()

    def test_components(self):
        print('''
    Testing Components
         (^_^)
    ''')
        print('Testing application components...\n')

        # Test database
        print('Testing database...')
        try:
            stats = self.scraper.get_database_stats()
            print(f'Database: OK (total: {stats["total_articles"]} articles)\n')
        except Exception as error:
            print(f'Database: Failed ({error})\n')

        # Test email connection
        print('Testing email connection...')
        email_ok = self.email_sender.test_connection()
        print(f'Email: {"OK" if email_ok else "Failed"}\n')

        # Test scraper
        print('Testing news scraper...')
        try:
            news = self.scraper.scrape_news(save_to_db=False)  # Don't save during test
            print(f'Scraper: OK (found {len(news)} items)\n')
        except Exception as error:
            print(f'Scraper: Failed ({error})\n')

        # Test AI (if API key provided)
        if self.ai_processor:
            print('Testing AI processor...')
            try:
                test_summary = self.ai_processor.create_tweet_like_summary({
                    'title': 'Test Sumo Tournament Results',
                    'url': 'https://example.com',
                    'content': 'Test content'
                })
                try:
                    print(f'AI: OK ({test_summary[:50]}...)\n')
                except UnicodeEncodeError:
                    print('AI: OK (summary contains special characters)\n')
            except Exception as error:
                try:
                    print(f'AI: Failed ({error})\n')
                except UnicodeEncodeError:
                    print('AI: Failed (Unicode error in response)\n')
        else:
            print('AI: Skipped (no API key)\n')


def show_help():
    help_text = """
    Sumo News Emailer Help
           (?)
    
Sumo News Emailer

Usage:
  python src/main.py           - Run the main application
  python src/main.py --test    - Test all components
  python src/main.py --dry-run - Generate email without sending (for testing)
  python src/main.py --help    - Show this help

Environment variables required:
  OPENAI_API_KEY    - Your OpenAI API key
  EMAIL_HOST        - SMTP server (e.g., smtp.gmail.com)
  EMAIL_PORT        - SMTP port (e.g., 587)
  EMAIL_USER        - Your email address
  EMAIL_PASS        - Your email password/app password
  EMAIL_TO          - Recipient email address

Copy .env.example to .env and fill in your values.
"""
    print(help_text)


if __name__ == '__main__':
    args = sys.argv[1:]
    app = SumoNewsApp()
    
    if '--test' in args:
        app.test_components()
    elif '--help' in args:
        show_help()
    elif '--dry-run' in args:
        app.run(dry_run=True)
    else:
        app.run()