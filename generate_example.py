#!/usr/bin/env python3
"""
Generate example email content for documentation purposes
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_processor import AIProcessor
from emailer import EmailSender

def create_sample_news_items():
    """Create sample news items for demonstration"""
    return [
        {
            'id': 1,
            'title': 'Terunofuji Wins July Grand Sumo Tournament',
            'url': 'https://www.sumo.or.jp/EnHonbashoMain/torikumi/1/15/',
            'content': 'Yokozuna Terunofuji claimed victory in the July Grand Sumo Tournament with an impressive 13-2 record, defeating Kotozakura in the final bout.',
            'source': 'Japan Sumo Association',
            'date': '2025-07-28',
            'summary': 'Terunofuji dominates July tournament with 13-2 record! The Mongolian yokozuna showed incredible strength, defeating Kotozakura in the championship bout. What a performance!',
            'raw_text': 'Terunofuji Wins July Grand Sumo Tournament'
        },
        {
            'id': 2,
            'title': 'Rising Star Onosato Promoted to Sekiwake',
            'url': 'https://www.sumo.or.jp/EnKyokai/information?id=700',
            'content': 'Young wrestler Onosato has been promoted to the sekiwake rank following his outstanding 11-4 performance in the previous tournament.',
            'source': 'Japan Sumo Association',
            'date': '2025-07-25',
            'summary': 'Young gun Onosato rockets to sekiwake! At just 24, this rising star earned promotion with an impressive 11-4 record. The future of sumo looks bright!',
            'raw_text': 'Rising Star Onosato Promoted to Sekiwake'
        },
        {
            'id': 3,
            'title': '2025 World Sumo Championships Announced',
            'url': 'https://ifs-sumo.org/championships-2025',
            'content': 'The International Federation of Sumo has announced the 2025 World Sumo Championships will be held in Osaka, Japan this October.',
            'source': 'IFS Sumo',
            'date': '2025-07-20',
            'summary': 'World Sumo Championships coming to Osaka! October 2025 will see international athletes compete on Japanese soil. Global sumo action awaits!',
            'raw_text': '2025 World Sumo Championships Announced'
        }
    ]

def generate_example_email():
    """Generate example email content"""
    
    print('''
    Example Email Generator
         (^_^)
    ''')
    print('Generating sample email content...\n')
    
    # Create sample data
    sample_items = create_sample_news_items()
    email_meta = {
        'subject': 'Sumo Weekly: Terunofuji Triumphs & Rising Stars!',
        'intro': 'Greetings sumo fans! This week brings championship glory, exciting promotions, and international tournament announcements. Here are your top sumo stories:'
    }
    
    print("=" * 60)
    print("EXAMPLE EMAIL SUBJECT:")
    print("=" * 60)
    print(email_meta['subject'])
    print()
    
    print("=" * 60)
    print("EXAMPLE EMAIL PREVIEW:")
    print("=" * 60)
    print("Subject:", email_meta['subject'])
    print("From: Sumo News Bot <sumo@example.com>")
    print("To: fan@example.com")
    print()
    print("Content Preview:")
    print("-" * 40)
    print(email_meta['intro'])
    print()
    
    for i, item in enumerate(sample_items, 1):
        print(f"{i}. {item['summary']}")
        print(f"   Date: {item['date']}")
        print(f"   Read more: {item['url']}")
        print(f"   Source: [{item['source']}]")
        print()
    
    print("-" * 40)
    print("This digest was automatically generated from multiple sumo news sources")
    print(f"Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}")
    print()
    print("To unsubscribe: Reply with 'UNSUBSCRIBE' or contact the sender.")
    print("We respect your privacy and email preferences.")
    
    # Create a simple HTML version without using the emailer class
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{email_meta['subject']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #d2691e; color: white; padding: 20px; text-align: center; }}
        .article {{ margin: 20px 0; padding: 15px; border-left: 4px solid #d2691e; background-color: #fafafa; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }}
        a {{ color: #d2691e; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Sumo Wrestling News</h1>
        <p>Your daily digest of sumo updates</p>
    </div>
    
    <p>{email_meta['intro']}</p>
    
    {''.join([f'<div class="article"><strong>{i+1}.</strong> {item["summary"]}<br><small>Date: {item["date"]} | Source: {item["source"]}</small><br><a href="{item["url"]}">Read full article →</a></div>' for i, item in enumerate(sample_items)])}
    
    <div class="footer">
        <p>This digest was automatically generated from multiple sumo news sources</p>
        <p>Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}</p>
        <p>To unsubscribe: Reply with "UNSUBSCRIBE" or contact the sender.</p>
    </div>
</body>
</html>
"""
    
    # Save HTML version to file
    with open('example_email.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n" + "=" * 60)
    print("FILES GENERATED:")
    print("=" * 60)
    print("+ example_email.html - Full HTML email preview")
    print("+ Preview content shown above")
    print()
    
    print("Example generation complete!")
    print("   Open example_email.html in your browser to see the full design.")
    
    return {
        'subject': email_meta['subject'],
        'html_file': 'example_email.html'
    }

if __name__ == "__main__":
    generate_example_email()