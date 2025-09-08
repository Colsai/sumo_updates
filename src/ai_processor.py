from openai import OpenAI
import time
import json
import re
from typing import List, Dict, Optional, Tuple
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

    def create_email_digest(self, summaries: List[Dict], sumo_tip: Dict = None) -> Dict[str, str]:
        try:
            news_content = '\n\n'.join([
                f"{i + 1}. {item['summary']}\n   📰 Read more: {item['url']}"
                for i, item in enumerate(summaries)
            ])

            # Include tip info in prompt if provided
            tip_info = ""
            if sumo_tip:
                tip_info = f"\n\nToday's Bite-sized Sumo tip: {sumo_tip['title']}"

            prompt = f"""Create an engaging email subject line and introduction for a sumo wrestling news digest. The email contains {len(summaries)} news items{" and includes an educational sumo tip" if sumo_tip else ""}. Make it enthusiastic and appealing to sumo fans.

News items:
{news_content}{tip_info}

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
    
    # Vector/Embedding methods
    def generate_embeddings(self, texts: List[str], model: str = 'text-embedding-3-small') -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            # Clean texts
            cleaned_texts = []
            for text in texts:
                # Remove excessive whitespace and limit length
                cleaned = ' '.join(text.split())[:8000]  # OpenAI embedding limit
                if cleaned.strip():
                    cleaned_texts.append(cleaned)
            
            if not cleaned_texts:
                return []
            
            response = self.openai.embeddings.create(
                model=model,
                input=cleaned_texts
            )
            
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as error:
            print(f'Error generating embeddings: {error}')
            return []
    
    def generate_single_embedding(self, text: str, model: str = 'text-embedding-3-small') -> Optional[List[float]]:
        """Generate embedding for a single text"""
        embeddings = self.generate_embeddings([text], model)
        return embeddings[0] if embeddings else None
    
    def extract_entities_and_topics(self, content: str, title: str = '') -> Tuple[List[str], List[str]]:
        """Extract sumo-related entities and topics from content"""
        try:
            text = f"{title} {content}"
            prompt = f"""Analyze this sumo wrestling news content and extract:
1. ENTITIES: Names of wrestlers, tournament names, locations, dates, organizations (JSA, etc.)
2. TOPICS: Key themes and topics (championships, injuries, retirements, techniques, rankings, etc.)

Content: {text[:2000]}

Return as JSON format:
{{
  "entities": ["entity1", "entity2", ...],
  "topics": ["topic1", "topic2", ...]
}}

Focus on sumo-specific terms and proper nouns."""

            response = self.openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=200,
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                data = json.loads(result)
                entities = data.get('entities', [])
                topics = data.get('topics', [])
                
                # Clean and filter results
                entities = [e.strip() for e in entities if e.strip()][:10]
                topics = [t.strip() for t in topics if t.strip()][:10]
                
                return entities, topics
                
            except json.JSONDecodeError:
                # Fallback: extract basic entities using regex
                return self._extract_entities_fallback(text)
            
        except Exception as error:
            print(f'Error extracting entities: {error}')
            return self._extract_entities_fallback(f"{title} {content}")
    
    def _extract_entities_fallback(self, text: str) -> Tuple[List[str], List[str]]:
        """Fallback entity extraction using regex patterns"""
        # Common sumo wrestling terms and patterns
        sumo_terms = [
            'yokozuna', 'ozeki', 'sekiwake', 'komusubi', 'maegashira', 
            'basho', 'tournament', 'makuuchi', 'juryo', 'makushita',
            'sumo', 'rikishi', 'wrestler', 'JSA', 'Japan Sumo Association'
        ]
        
        # Find capitalized words (potential names/places)
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter sumo terms
        found_terms = [term for term in sumo_terms if term.lower() in text.lower()]
        
        entities = list(set(names[:5] + found_terms[:5]))
        topics = found_terms[:5]
        
        return entities, topics
    
    def analyze_article_relationships(self, article_content: str, 
                                    similar_articles: List[Dict]) -> List[Dict]:
        """Analyze relationships between current article and similar ones"""
        if not similar_articles:
            return []
        
        try:
            similar_summaries = []
            for i, article in enumerate(similar_articles[:3]):  # Limit to top 3
                similar_summaries.append(f"{i+1}. {article['title']}")
            
            prompt = f"""Analyze the relationship between this new article and similar existing articles:

NEW ARTICLE: {article_content[:1000]}

SIMILAR ARTICLES:
{chr(10).join(similar_summaries)}

For each similar article, determine the relationship type and confidence (0-1):
- 'duplicate': Same story, different source
- 'update': Follow-up or update to previous story  
- 'related': Similar topic but different story
- 'reference': References or mentions the other story

Return JSON format:
{{
  "relationships": [
    {{"article_index": 1, "type": "update", "confidence": 0.85, "reason": "brief explanation"}},
    ...
  ]
}}"""

            response = self.openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=300,
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()
            
            try:
                data = json.loads(result)
                relationships = []
                
                for rel in data.get('relationships', []):
                    if 0 <= rel.get('article_index', 0) - 1 < len(similar_articles):
                        idx = rel['article_index'] - 1
                        relationships.append({
                            'article_id': similar_articles[idx].get('id'),
                            'type': rel.get('type', 'related'),
                            'confidence': rel.get('confidence', 0.5),
                            'reason': rel.get('reason', ''),
                            'title': similar_articles[idx].get('title', '')
                        })
                
                return relationships
                
            except json.JSONDecodeError:
                return []
            
        except Exception as error:
            print(f'Error analyzing relationships: {error}')
            return []
    
    def generate_tags_for_article(self, title: str, content: str, 
                                 entities: List[str] = None) -> Tuple[List[str], List[float]]:
        """Generate smart tags for an article using AI and pattern matching"""
        try:
            # First use pattern-based tag generation as fallback
            pattern_tags = self._generate_pattern_tags(title, content, entities)
            
            # Then enhance with AI-generated tags
            text = f"{title} {content}"
            prompt = f"""Analyze this sumo wrestling article and generate relevant tags.

Title: {title}
Content: {content[:1500]}

Generate tags in these categories:
- Tournament: basho names, tournament types, dates
- Wrestler: names of wrestlers mentioned
- Rank: yokozuna, ozeki, sekiwake, etc.
- Event: promotion, retirement, injury, victory, etc. 
- Location: tokyo, osaka, nagoya, kyushu, etc.
- Content-Type: interview, schedule, results, news, etc.

Return as JSON:
{{
  "tags": ["tag1", "tag2", ...],
  "confidence_scores": [0.9, 0.8, ...]
}}

Focus on specific, searchable terms. Limit to 10 most relevant tags."""

            response = self.openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=200,
                temperature=0.3
            )

            result_text = response.choices[0].message.content.strip()
            
            try:
                result = json.loads(result_text)
                ai_tags = result.get('tags', [])
                ai_scores = result.get('confidence_scores', [])
                
                # Clean and validate AI tags
                clean_ai_tags = []
                clean_ai_scores = []
                
                for i, tag in enumerate(ai_tags):
                    if tag and isinstance(tag, str) and len(tag.strip()) > 1:
                        clean_tag = tag.lower().strip()
                        clean_ai_tags.append(clean_tag)
                        
                        # Use provided confidence or default
                        confidence = ai_scores[i] if i < len(ai_scores) else 0.8
                        clean_ai_scores.append(confidence)
                
                # Combine pattern tags with AI tags (prioritize AI tags)
                combined_tags = []
                combined_scores = []
                
                # Add AI tags first
                for i, tag in enumerate(clean_ai_tags):
                    if tag not in combined_tags:
                        combined_tags.append(tag)
                        combined_scores.append(clean_ai_scores[i])
                
                # Add pattern tags if not already present
                for tag in pattern_tags:
                    if tag not in combined_tags and len(combined_tags) < 15:
                        combined_tags.append(tag)
                        combined_scores.append(0.7)  # Lower confidence for pattern tags
                
                return combined_tags[:12], combined_scores[:12]  # Limit to 12 tags
                
            except json.JSONDecodeError:
                # Fallback to pattern tags only
                print("AI tag generation failed, using pattern tags")
                scores = [0.7] * len(pattern_tags)
                return pattern_tags, scores
            
        except Exception as error:
            print(f'Error generating tags: {error}')
            # Fallback to pattern tags
            pattern_tags = self._generate_pattern_tags(title, content, entities)
            scores = [0.6] * len(pattern_tags)
            return pattern_tags, scores
    
    def _generate_pattern_tags(self, title: str, content: str, entities: List[str] = None) -> List[str]:
        """Generate tags using pattern matching (fallback method)"""
        tags = []
        text = f"{title} {content}".lower()
        
        # Tournament/Event detection
        if any(term in text for term in ['basho', 'tournament', 'championship']):
            if 'september' in text:
                tags.append('september-basho')
            elif 'autumn' in text:
                tags.append('autumn-tournament')
            else:
                tags.append('tournament')
        
        # Rank detection
        rank_patterns = ['yokozuna', 'ozeki', 'sekiwake', 'komusubi', 'maegashira']
        for rank in rank_patterns:
            if rank in text:
                tags.append(rank)
        
        # Event type detection
        if 'promoted' in text or 'promotion' in text:
            tags.append('promotion')
        if 'retired' in text or 'retirement' in text:
            tags.append('retirement')
        if 'injured' in text or 'injury' in text:
            tags.append('injury')
        if any(term in text for term in ['victory', 'win', 'champion']):
            tags.append('victory')
        if 'charity' in text or 'support' in text:
            tags.append('charity')
        
        # Location detection
        locations = ['tokyo', 'osaka', 'nagoya', 'kyushu', 'london']
        for location in locations:
            if location in text:
                tags.append(location)
        
        # Content type detection
        if 'interview' in text:
            tags.append('interview')
        if 'schedule' in text:
            tags.append('schedule')
        if 'banzuke' in text:
            tags.append('banzuke')
        if 'highlights' in text:
            tags.append('highlights')
        if 'results' in text:
            tags.append('results')
        
        # Add entity-based tags
        if entities:
            for entity in entities[:3]:  # Limit to top 3 entities
                if entity and len(entity.strip()) > 2:
                    clean_entity = entity.lower().strip()
                    if clean_entity not in tags:
                        tags.append(clean_entity)
        
        # Year tags
        for year in ['2024', '2025', '2026']:
            if year in text:
                tags.append(year)
        
        # Remove duplicates and clean
        unique_tags = []
        for tag in tags:
            clean_tag = tag.strip().lower()
            if clean_tag and clean_tag not in unique_tags and len(clean_tag) > 1:
                unique_tags.append(clean_tag)
        
        return unique_tags[:10]  # Limit to 10 tags
    
    def select_sumo_tip(self, tip_manager) -> Optional[Dict]:
        """Select an appropriate sumo tip for the email"""
        try:
            # Try to get an unused tip from different categories in order of preference
            categories = ['history', 'culture', 'techniques', 'tournaments', 'facts', 'modern']
            
            for category in categories:
                tip = tip_manager.get_unused_tip(category=category, days_since_last_use=30)
                if tip:
                    return tip
            
            # If no category-specific tips available, get any unused tip
            tip = tip_manager.get_unused_tip(days_since_last_use=30)
            if tip:
                return tip
            
            # As last resort, get any random tip (least recently used)
            tip = tip_manager.get_unused_tip(days_since_last_use=1)
            return tip
            
        except Exception as error:
            print(f'Error selecting sumo tip: {error}')
            return None
    
    def format_sumo_tip(self, tip: Dict) -> Dict[str, str]:
        """Format sumo tip for email inclusion"""
        if not tip:
            return None
            
        try:
            # Format the tip content for email
            formatted_tip = {
                'title': tip['title'],
                'content': tip['content'],
                'category': tip['category'].title(),
                'difficulty': tip['difficulty_level'].title(),
                'html_content': f"""
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #d4af37; margin: 20px 0;">
                        <h3 style="color: #d4af37; margin: 0 0 10px 0;">{tip['title']}</h3>
                        <p style="margin: 0; line-height: 1.5;">{tip['content']}</p>
                        <small style="color: #6c757d; font-style: italic;">Category: {tip['category'].title()}</small>
                    </div>
                """,
                'text_content': f"""
BITE-SIZED SUMO: {tip['title']}
{'-' * (len(tip['title']) + 18)}
{tip['content']}

Category: {tip['category'].title()}
                """
            }
            
            return formatted_tip
            
        except Exception as error:
            print(f'Error formatting sumo tip: {error}')
            return None