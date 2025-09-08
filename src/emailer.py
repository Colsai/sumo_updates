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

    def send_news_digest(self, summaries: List[Dict], email_meta: Dict[str, str], sumo_tip: Dict = None, dry_run: bool = False) -> Dict:
        try:
            if not summaries:
                print('No news to send')
                return {'success': False, 'error': 'No news items'}

            html_content = self._generate_html_email(summaries, email_meta, sumo_tip)
            text_content = self._generate_text_email(summaries, email_meta, sumo_tip)

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

    def _generate_html_email(self, summaries: List[Dict], email_meta: Dict[str, str], sumo_tip: Dict = None) -> str:
        # Generate news items with modern card design
        news_items = ''
        for i, item in enumerate(summaries):
            # Parse and format article date
            try:
                if 'T' in item['date']:
                    article_date = datetime.fromisoformat(item['date'].replace('Z', '+00:00')).strftime('%B %d, %Y')
                else:
                    article_date = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%B %d, %Y')
            except:
                article_date = item['date']

            news_items += f'''
          <div style="margin-bottom: 24px; background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #f0f0f0;">
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
              <div style="background: linear-gradient(135deg, #e74c3c, #d35400); color: white; font-weight: bold; font-size: 14px; padding: 4px 12px; border-radius: 20px; margin-right: 12px;">
                #{i + 1}
              </div>
              <div style="font-size: 13px; color: #7f8c8d; font-weight: 500;">
                {article_date}
              </div>
            </div>
            <div style="font-size: 16px; line-height: 1.5; color: #2c3e50; margin-bottom: 16px; font-weight: 400;">
              {item['summary']}
            </div>
            <div>
              <a href="{item['url']}" style="display: inline-flex; align-items: center; background: linear-gradient(135deg, #3498db, #2980b9); color: white; text-decoration: none; font-weight: 600; font-size: 14px; padding: 10px 18px; border-radius: 25px; transition: all 0.3s ease;">
                <span style="margin-right: 6px;">📖</span> Read Article
              </a>
            </div>
          </div>'''

        # Current date for newsletter publication
        publication_date = datetime.now().strftime('%B %d, %Y')
        publication_weekday = datetime.now().strftime('%A')

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{email_meta['subject']}</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; line-height: 1.6;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
    
    <!-- Header Section -->
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 0; text-align: center;">
      <img src="cid:header_image" alt="Sumo Updates Newsletter" style="max-width: 100%; height: auto; display: block;">
    </div>
    
    <!-- Publication Date Header -->
    <div style="background: linear-gradient(135deg, #e74c3c, #d35400); color: white; text-align: center; padding: 16px 24px;">
      <div style="font-size: 14px; font-weight: 600; opacity: 0.9; margin-bottom: 4px;">
        📅 PUBLISHED
      </div>
      <div style="font-size: 18px; font-weight: 700; letter-spacing: 0.5px;">
        {publication_weekday}, {publication_date}
      </div>
    </div>
    
    <!-- Main Content -->
    <div style="padding: 32px 24px; background-color: #ffffff;">
      
      <!-- Introduction -->
      <div style="text-align: center; margin-bottom: 40px; padding: 24px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 16px; border-left: 4px solid #e74c3c;">
        <h1 style="font-size: 24px; font-weight: 700; color: #2c3e50; margin: 0 0 16px 0; line-height: 1.3;">
          🤼‍♂️ Sumo Wrestling Digest
        </h1>
        <p style="font-size: 16px; color: #5d6d7e; margin: 0; line-height: 1.5;">
          {email_meta['intro']}
        </p>
      </div>
      
      <!-- News Articles Section -->
      <div style="margin-bottom: 40px;">
        <h2 style="font-size: 22px; font-weight: 700; color: #2c3e50; margin: 0 0 24px 0; padding-bottom: 12px; border-bottom: 3px solid #e74c3c;">
          📰 Latest News
        </h2>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px;">
          {news_items}
        </div>
      </div>
      
      <!-- Bite-sized Sumo Section -->
      {self._generate_sumo_tip_html(sumo_tip) if sumo_tip else ''}
      
    </div>
    
    <!-- Footer -->
    <div style="background-color: #2c3e50; color: #bdc3c7; padding: 32px 24px; text-align: center;">
      <div style="margin-bottom: 20px;">
        <div style="font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 8px;">
          🤼‍♂️ Sumo Wrestling Digest
        </div>
        <div style="font-size: 14px; opacity: 0.8;">
          Your source for authentic sumo wrestling news and insights
        </div>
      </div>
      
      <div style="border-top: 1px solid #34495e; padding-top: 20px; font-size: 13px; opacity: 0.7;">
        <p style="margin: 0 0 8px 0;">
          This digest was curated from trusted sumo wrestling sources
        </p>
        <p style="margin: 0 0 16px 0;">
          Generated on {publication_date}
        </p>
        <p style="margin: 0; font-size: 12px;">
          To unsubscribe, reply with "UNSUBSCRIBE" | We respect your privacy
        </p>
      </div>
    </div>
    
  </div>
</body>
</html>'''

    def _generate_text_email(self, summaries: List[Dict], email_meta: Dict[str, str], sumo_tip: Dict = None) -> str:
        # Publication date
        publication_date = datetime.now().strftime('%B %d, %Y')
        publication_weekday = datetime.now().strftime('%A')
        
        # Format news items
        news_items = []
        for i, item in enumerate(summaries):
            try:
                if 'T' in item['date']:
                    date_str = datetime.fromisoformat(item['date'].replace('Z', '+00:00')).strftime('%B %d, %Y')
                else:
                    date_str = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%B %d, %Y')
            except:
                date_str = item['date']
                
            news_items.append(
                f"#{i + 1} | {date_str}\n{item['summary']}\nRead more: {item['url']}"
            )

        news_content = '\n\n'.join(news_items)
        
        # Add sumo tip if provided
        sumo_tip_content = ''
        if sumo_tip:
            tip_title = sumo_tip.get('title', 'Sumo Fact')
            sumo_tip_content = f'''

{'=' * 60}
🥇 BITE-SIZED SUMO: {tip_title.upper()}
{'=' * 60}

{sumo_tip.get('content', 'Educational sumo content')}

📚 Category: {sumo_tip.get('category', 'General').title()}
🎯 Level: {sumo_tip.get('difficulty_level', 'Beginner').title()}
{'=' * 60}

'''
        
        return f'''🤼‍♂️ SUMO WRESTLING DIGEST
📅 PUBLISHED: {publication_weekday}, {publication_date}

{email_meta['intro']}

📰 LATEST NEWS
{'-' * 50}

{news_content}{sumo_tip_content}

{'*' * 60}
This digest was curated from trusted sumo wrestling sources
Generated on {publication_date}

To unsubscribe: Reply with "UNSUBSCRIBE"
We respect your privacy and email preferences.
{'*' * 60}'''

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
            
            # Save HTML version for easy viewing (with base64 embedded image)
            html_filename = f'email_{timestamp}.html'
            html_path = os.path.join(self.archives_path, html_filename)
            
            # Create browser-viewable HTML with embedded image
            browser_html = self._create_browser_viewable_html(html_content)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(browser_html)
            
            print(f'Email archived: {json_filename} and {html_filename}')
            
        except Exception as error:
            print(f'Warning: Failed to archive email: {error}')
    
    def _generate_sumo_tip_html(self, sumo_tip: Dict) -> str:
        """Generate HTML section for sumo tip"""
        if not sumo_tip:
            return ''
        
        return f'''
      <!-- Educational Section -->
      <div style="margin-bottom: 40px;">
        <h2 style="font-size: 22px; font-weight: 700; color: #2c3e50; margin: 0 0 24px 0; padding-bottom: 12px; border-bottom: 3px solid #f39c12;">
          🥇 Bite-sized Sumo
        </h2>
        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border-radius: 16px; padding: 28px; border-left: 6px solid #f39c12; position: relative; overflow: hidden;">
          <div style="position: absolute; top: -10px; right: -10px; width: 60px; height: 60px; background: rgba(243, 156, 18, 0.1); border-radius: 50%; z-index: 0;"></div>
          <div style="position: relative; z-index: 1;">
            <h3 style="color: #e67e22; margin: 0 0 16px 0; font-size: 20px; font-weight: 700;">
              {sumo_tip.get('title', 'Sumo Fact')}
            </h3>
            <p style="margin: 0 0 20px 0; line-height: 1.6; color: #2c3e50; font-size: 16px;">
              {sumo_tip.get('content', 'Educational sumo content')}
            </p>
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
              <div style="background: rgba(230, 126, 34, 0.15); color: #d35400; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                📚 {sumo_tip.get('category', 'General').title()}
              </div>
              <div style="background: rgba(230, 126, 34, 0.15); color: #d35400; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                🎯 {sumo_tip.get('difficulty_level', 'Beginner').title()}
              </div>
            </div>
          </div>
        </div>
      </div>'''
    
    def _create_browser_viewable_html(self, html_content: str) -> str:
        """Convert email HTML with cid: references to browser-viewable HTML with base64 embedded images"""
        try:
            if os.path.exists(self.header_image_path):
                # Read and encode the image as base64
                with open(self.header_image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                # Replace cid: reference with base64 data URL
                data_url = f'data:image/png;base64,{img_base64}'
                browser_html = html_content.replace('src="cid:header_image"', f'src="{data_url}"')
                
                return browser_html
            else:
                # If image doesn't exist, replace with placeholder or remove
                return html_content.replace('<img src="cid:header_image" alt="Sumo Updates Newsletter" style="max-width: 100%; height: auto; display: block; margin: 0 auto;">', 
                                          '<div style="text-align: center; padding: 20px; background: #f0f0f0; color: #666;">📸 Sumo Updates Newsletter Banner</div>')
        except Exception as e:
            print(f'Warning: Could not embed image in archived HTML: {e}')
            return html_content