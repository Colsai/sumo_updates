from openai import OpenAI
import time
from typing import List, Dict
from datetime import datetime


class AIProcessor:
    def __init__(self, api_key: str):
        self.openai = OpenAI(api_key=api_key)

    def create_tweet_like_summary(self, news_item: Dict) -> str:
        try:
            prompt = f"""Convert this sumo wrestling news into a concise, engaging tweet-like summary (max 280 characters). Make it informative but casual and exciting:

Title: {news_item['title']}
URL: {news_item['url']}
Additional context: {news_item.get('content', '')}

Format the response as a single tweet that captures the essence of the news. Include relevant sumo terminology and emojis if appropriate. Make it exciting for sumo fans!"""

            response = self.openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=100,
                temperature=0.7
            )

            summary = response.choices[0].message.content.strip()
            
            # Ensure it's under 280 characters
            return summary[:277] + '...' if len(summary) > 280 else summary
            
        except Exception as error:
            print(f'Error creating AI summary: {error}')
            return self._create_fallback_summary(news_item)

    def _create_fallback_summary(self, news_item: Dict) -> str:
        title = news_item['title']
        if len(title) <= 280:
            return f"🥋 {title}"
        return f"🥋 {title[:275]}..."

    def process_batch(self, news_items: List[Dict]) -> List[Dict]:
        summaries = []
        
        for item in news_items:
            print(f"Processing: {item['title']}")
            summary = self.create_tweet_like_summary(item)
            
            summaries.append({
                **item,
                'summary': summary,
                'processed_at': datetime.now().isoformat()
            })
            
            # Rate limiting - wait 1 second between API calls
            time.sleep(1)
        
        return summaries

    def create_email_digest(self, summaries: List[Dict]) -> Dict[str, str]:
        try:
            news_content = '\n\n'.join([
                f"{i + 1}. {item['summary']}\n   📰 Read more: {item['url']}"
                for i, item in enumerate(summaries)
            ])

            prompt = f"""Create an engaging email subject line and introduction for a sumo wrestling news digest. The email contains {len(summaries)} news items. Make it enthusiastic and appealing to sumo fans.

News items:
{news_content}

Provide:
1. SUBJECT: [compelling subject line under 50 characters]
2. INTRO: [2-3 sentence introduction paragraph]"""

            response = self.openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=150,
                temperature=0.7
            )

            result = response.choices[0].message.content.strip()
            lines = result.split('\n')
            
            subject = 'Sumo Wrestling News Update'
            intro = 'Here are the latest updates from the world of sumo wrestling!'
            
            for line in lines:
                line = line.strip()
                if line.startswith('SUBJECT:'):
                    subject = line.replace('SUBJECT:', '').strip()
                elif line.startswith('INTRO:'):
                    intro = line.replace('INTRO:', '').strip()

            return {'subject': subject, 'intro': intro}
            
        except Exception as error:
            print(f'Error creating email digest: {error}')
            return {
                'subject': 'Sumo Wrestling News Update',
                'intro': 'Here are the latest updates from the world of sumo wrestling!'
            }