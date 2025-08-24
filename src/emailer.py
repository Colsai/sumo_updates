import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime


class EmailSender:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.smtp_server = None

    def send_news_digest(self, summaries: List[Dict], email_meta: Dict[str, str]) -> Dict:
        try:
            if not summaries:
                print('No news to send')
                return {'success': False, 'error': 'No news items'}

            html_content = self._generate_html_email(summaries, email_meta)
            text_content = self._generate_text_email(summaries, email_meta)

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f'"Sumo News Bot" <{self.config["user"]}>'
            msg['To'] = self.config['to']
            msg['Subject'] = email_meta['subject']

            # Attach both plain text and HTML versions
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
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
          📅 {datetime.fromisoformat(item['date'].replace('Z', '+00:00')).strftime('%B %d, %Y') if 'T' not in item['date'] else datetime.strptime(item['date'], '%Y-%m-%d').strftime('%B %d, %Y')}
        </div>
        <div>
          <a href="{item['url']}" style="color: #d2691e; text-decoration: none; font-weight: bold;">
            📰 Read full article →
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
  <div style="background-color: #d2691e; color: white; padding: 20px; text-align: center; margin-bottom: 30px;">
    <h1 style="margin: 0; font-size: 24px;">🥋 Sumo Wrestling News</h1>
    <p style="margin: 10px 0 0 0; font-size: 14px;">Your daily digest of sumo updates</p>
  </div>
  
  <div style="margin-bottom: 20px;">
    <p style="font-size: 16px; margin-bottom: 20px;">{email_meta['intro']}</p>
  </div>
  
  {news_items}
  
  <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px;">
    <p>This digest was automatically generated from <a href="https://www.sumo.or.jp/En/" style="color: #d2691e;">sumo.or.jp</a></p>
    <p>Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}</p>
  </div>
</body>
</html>'''

    def _generate_text_email(self, summaries: List[Dict], email_meta: Dict[str, str]) -> str:
        news_items = []
        for i, item in enumerate(summaries):
            date_str = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%B %d, %Y') if 'T' not in item['date'] else item['date']
            news_items.append(
                f"{i + 1}. {item['summary']}\n   📅 {date_str}\n   📰 {item['url']}"
            )

        news_content = '\n\n'.join(news_items)
        
        return f'''🥋 SUMO WRESTLING NEWS DIGEST

{email_meta['intro']}

{news_content}

---
This digest was automatically generated from sumo.or.jp
Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}'''

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