import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import List, Dict
from datetime import datetime
import base64
import os
import json
import time


class EmailSender:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.smtp_server = None
        self.header_image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'images', 'b3f127bc-12dd-4fcc-ac1c-c7ba53c1034b.png')
        self.archives_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'archives')

    def send_news_digest(self, summaries: List[Dict], email_meta: Dict[str, str], dry_run: bool = False) -> Dict:
        try:
            if not summaries:
                print('No news to send')
                return {'success': False, 'error': 'No news items'}

            html_content = self._generate_html_email(summaries, email_meta)
            text_content = self._generate_text_email(summaries, email_meta)

            # Save the generated email to archives
            self._save_email_archive(summaries, email_meta, html_content, text_content)

            # Create message with mixed content (for images and alternative text/html)
            msg = MIMEMultipart('mixed')
            msg['From'] = f'"Sumo News Bot" <{self.config["user"]}>'
            msg['To'] = self.config['to']
            msg['Subject'] = email_meta['subject']

            # Create alternative container for text and HTML
            msg_alternative = MIMEMultipart('alternative')
            
            # Attach both plain text and HTML versions
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg_alternative.attach(text_part)
            msg_alternative.attach(html_part)
            
            # Attach the alternative container to main message
            msg.attach(msg_alternative)
            
            # Attach header image if it exists
            if os.path.exists(self.header_image_path):
                with open(self.header_image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', '<header_image>')
                    img.add_header('Content-Disposition', 'inline', filename='header.png')
                    msg.attach(img)

            # Send email or simulate in dry-run mode
            if dry_run:
                print('DRY RUN: Email content generated but not sent')
                message_id = 'dry-run-' + str(int(time.time()))
                print(f'Dry run completed with simulated message ID: {message_id}')
                return {'success': True, 'message_id': message_id, 'dry_run': True}
            else:
                print('Sending email...')
                with smtplib.SMTP(self.config['host'], int(self.config['port'])) as server:
                    server.starttls()
                    server.login(self.config['user'], self.config['pass'])
                    message_id = server.send_message(msg)
                
                print(f'Email sent successfully: {message_id}')
                return {'success': True, 'message_id': str(message_id)}
            
        except Exception as error:
            print(f'Error sending email: {error}')
            return {'success': False, 'error': str(error)}

    def _generate_html_email(self, summaries: List[Dict], email_meta: Dict[str, str]) -> str:
        news_items = ''
        for i, item in enumerate(summaries):
            news_items += f'''
      <div style="margin-bottom: 20px; padding: 15px; border-left: 4px solid #d2691e; background-color: #fafafa;">
        <div style="font-size: 16px; margin-bottom: 8px; color: #333;">
          <strong>{i + 1}.</strong> {item['summary']}
        </div>
        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
          Date: {datetime.fromisoformat(item['date'].replace('Z', '+00:00')).strftime('%B %d, %Y') if 'T' not in item['date'] else datetime.strptime(item['date'], '%Y-%m-%d').strftime('%B %d, %Y')}
        </div>
        <div>
          <a href="{item['url']}" style="color: #d2691e; text-decoration: none; font-weight: bold;">
            >> Read full article
          </a>
        </div>
      </div>'''

        return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{email_meta['subject']}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="text-align: center; margin-bottom: 30px;">
    <img src="cid:header_image" alt="Sumo Updates Newsletter" style="max-width: 100%; height: auto; display: block; margin: 0 auto;">
  </div>
  
  <div style="margin-bottom: 20px;">
    <p style="font-size: 16px; margin-bottom: 20px;">{email_meta['intro']}</p>
  </div>
  
  {news_items}
  
  <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px;">
    <p>This digest was automatically generated from multiple sumo news sources</p>
    <p>Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}</p>
    <p style="margin-top: 15px; font-size: 11px;">
      To unsubscribe from these emails, please reply with "UNSUBSCRIBE" or contact the sender.<br>
      This is an automated digest service. We respect your privacy and email preferences.
    </p>
  </div>
</body>
</html>'''

    def _generate_text_email(self, summaries: List[Dict], email_meta: Dict[str, str]) -> str:
        news_items = []
        for i, item in enumerate(summaries):
            date_str = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%B %d, %Y') if 'T' not in item['date'] else item['date']
            news_items.append(
                f"{i + 1}. {item['summary']}\n   Date: {date_str}\n   Link: {item['url']}"
            )

        news_content = '\n\n'.join(news_items)
        
        return f'''SUMO WRESTLING NEWS DIGEST

{email_meta['intro']}

{news_content}

---
This digest was automatically generated from multiple sumo news sources
Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}

To unsubscribe: Reply with "UNSUBSCRIBE" or contact the sender.
We respect your privacy and email preferences.'''

    def test_connection(self) -> bool:
        try:
            with smtplib.SMTP(self.config['host'], int(self.config['port'])) as server:
                server.starttls()
                server.login(self.config['user'], self.config['pass'])
                print('Email connection verified successfully')
                return True
        except Exception as error:
            print(f'Email connection failed: {error}')
            return False

    def _save_email_archive(self, summaries: List[Dict], email_meta: Dict[str, str], html_content: str, text_content: str):
        """Save the generated email to the archives folder"""
        try:
            # Ensure archives directory exists
            os.makedirs(self.archives_path, exist_ok=True)
            
            # Create timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create archive data
            archive_data = {
                'timestamp': datetime.now().isoformat(),
                'subject': email_meta['subject'],
                'intro': email_meta['intro'],
                'recipient': self.config.get('to', 'unknown'),
                'article_count': len(summaries),
                'articles': summaries,
                'html_content': html_content,
                'text_content': text_content
            }
            
            # Save as JSON file
            json_filename = f'email_{timestamp}.json'
            json_path = os.path.join(self.archives_path, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, indent=2, ensure_ascii=False)
            
            # Save HTML version for easy viewing
            html_filename = f'email_{timestamp}.html'
            html_path = os.path.join(self.archives_path, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f'Email archived: {json_filename} and {html_filename}')
            
        except Exception as error:
            print(f'Warning: Failed to archive email: {error}')