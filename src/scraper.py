import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional
import time
from database import NewsDatabase


class SumoNewsScraper:
    def __init__(self, db_path: str = 'sumo_news.db'):
        self.sources = [
            {
                'name': 'Japan Sumo Association',
                'url': 'https://www.sumo.or.jp/En/',
                'parser': self._parse_sumo_org
            },
            {
                'name': 'Japan Times Sumo',
                'url': 'https://www.japantimes.co.jp/sports/sumo/',
                'parser': self._parse_japan_times
            },
            {
                'name': 'IFS Sumo',
                'url': 'http://www.ifs-sumo.org/',
                'parser': self._parse_ifs_sumo
            }
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.db = NewsDatabase(db_path)

    def scrape_news(self, save_to_db: bool = True) -> List[Dict]:
        all_news = []
        
        for source in self.sources:
            print(f'  Fetching from {source["name"]}... (o_o)')
            try:
                news_items = source['parser'](source['url'])
                for item in news_items:
                    item['source'] = source['name']
                all_news.extend(news_items)
                
                # Rate limiting between sources
                time.sleep(2)
                
            except Exception as error:
                print(f'Error scraping {source["name"]}: {error}')
                continue

        # Remove duplicates and filter relevant news
        unique_news = self._remove_duplicates(all_news)
        relevant_news = self._filter_relevant_news(unique_news)
        
        if save_to_db and relevant_news:
            new_articles = self.db.save_articles(relevant_news)
            print(f'Saved {new_articles} new articles to database')
        
        print(f'Found {len(relevant_news)} total news items from all sources')
        return relevant_news[:10]  # Return top 10 items from all sources

    def get_unprocessed_articles(self, limit: int = 10) -> List[Dict]:
        """Get unprocessed articles from database for email digest"""
        articles = self.db.get_unprocessed_articles(limit)
        
        # Convert database format to scraper format
        formatted_articles = []
        for article in articles:
            formatted_articles.append({
                'id': article['id'],
                'title': article['title'],
                'url': article['url'],
                'content': article['content'],
                'source': article['source'],
                'date': article['article_date'] or article['scraped_at'][:10],
                'raw_text': article['title']
            })
        
        return formatted_articles

    def mark_articles_processed(self, articles: List[Dict], summaries: List[str] = None):
        """Mark articles as processed in the database"""
        article_ids = [article['id'] for article in articles if 'id' in article]
        if article_ids:
            self.db.mark_as_processed(article_ids, summaries)

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        return self.db.get_stats()

    def _parse_sumo_org(self, url: str) -> List[Dict]:
        """Parse news from Japan Sumo Association website"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []

            # Look for news items in various sections
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                href = link['href']
                
                if text and self._is_news_content(text, href):
                    news_items.append({
                        'title': text,
                        'url': self._resolve_url(href, 'https://www.sumo.or.jp'),
                        'date': self._extract_date(text) or datetime.now().strftime('%Y-%m-%d'),
                        'raw_text': text
                    })

            # Also look for specific news sections
            for item in soup.find_all(['div', 'section'], class_=re.compile(r'news|what-new')):
                link = item.find('a', href=True)
                if link:
                    title = link.get_text(strip=True) or item.get_text(strip=True)
                    if title:
                        news_items.append({
                            'title': title,
                            'url': self._resolve_url(link['href'], 'https://www.sumo.or.jp'),
                            'date': self._extract_date(title) or datetime.now().strftime('%Y-%m-%d'),
                            'raw_text': title
                        })

            return news_items

        except Exception as error:
            print(f'Error parsing sumo.or.jp: {error}')
            return []

    def _parse_japan_times(self, url: str) -> List[Dict]:
        """Parse news from Japan Times sumo section"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []

            # Look for article links - Japan Times uses specific selectors
            articles = soup.find_all(['article', 'div'], class_=re.compile(r'article|post|story|headline'))
            
            for article in articles:
                # Find title and link
                title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|headline|head'))
                if not title_elem:
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                
                if title_elem:
                    link = title_elem.find('a', href=True)
                    if not link:
                        link = article.find('a', href=True)
                    
                    if link:
                        title = title_elem.get_text(strip=True)
                        if title and len(title) > 10:
                            # Extract date
                            date_elem = article.find(['time', 'span'], class_=re.compile(r'date|time'))
                            date_str = datetime.now().strftime('%Y-%m-%d')
                            if date_elem:
                                date_text = date_elem.get_text(strip=True)
                                extracted_date = self._extract_date(date_text)
                                if extracted_date:
                                    date_str = extracted_date
                            
                            news_items.append({
                                'title': title,
                                'url': self._resolve_url(link['href'], 'https://www.japantimes.co.jp'),
                                'date': date_str,
                                'raw_text': title
                            })

            # Also look for simpler link structures
            for link in soup.find_all('a', href=True):
                if '/sports/sumo/' in link['href'] and link['href'] != url:
                    text = link.get_text(strip=True)
                    if text and 20 < len(text) < 200 and any(keyword in text.lower() for keyword in 
                        ['sumo', 'wrestler', 'tournament', 'basho', 'yokozuna', 'ozeki']):
                        news_items.append({
                            'title': text,
                            'url': self._resolve_url(link['href'], 'https://www.japantimes.co.jp'),
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'raw_text': text
                        })

            return news_items

        except Exception as error:
            print(f'Error parsing Japan Times: {error}')
            return []

    def _parse_ifs_sumo(self, url: str) -> List[Dict]:
        """Parse news from IFS Sumo website"""
        try:
            # Try different approaches as the site might have SSL issues
            session = requests.Session()
            session.verify = False  # Skip SSL verification for this problematic site
            
            try:
                response = session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
            except:
                # Fallback: try without SSL verification
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = requests.get(url, headers=self.headers, verify=False, timeout=10)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []

            # Look for news items - IFS typically has simple structure
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                href = link['href']
                
                if text and self._is_news_content(text, href):
                    news_items.append({
                        'title': text,
                        'url': self._resolve_url(href, 'http://www.ifs-sumo.org'),
                        'date': self._extract_date(text) or datetime.now().strftime('%Y-%m-%d'),
                        'raw_text': text
                    })

            # Look for specific content areas
            content_areas = soup.find_all(['div', 'section', 'article'], 
                                        class_=re.compile(r'content|news|main|post'))
            for area in content_areas:
                links = area.find_all('a', href=True)
                for link in links:
                    text = link.get_text(strip=True)
                    if text and 15 < len(text) < 200:
                        news_items.append({
                            'title': text,
                            'url': self._resolve_url(link['href'], 'http://www.ifs-sumo.org'),
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'raw_text': text
                        })

            return news_items

        except Exception as error:
            print(f'Error parsing IFS Sumo: {error}')
            return []

    def _is_news_content(self, text: str, href: str) -> bool:
        news_keywords = [
            'tournament', 'champion', 'promotion', 'sumo', 'wrestler',
            'bout', 'winner', 'result', 'ranking', 'ceremony', 'yokozuna',
            'ozeki', 'sekiwake', 'komusubi', 'maegashira', 'juryo'
        ]
        
        text_lower = text.lower()
        href_lower = href.lower()
        
        return (any(keyword in text_lower or keyword in href_lower for keyword in news_keywords) 
                and 10 < len(text) < 200)

    def _extract_date(self, text: str) -> Optional[str]:
        date_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})|(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        match = re.search(date_pattern, text)
        if match:
            try:
                date_str = match.group(0)
                # Try to parse and format the date
                for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y'):
                    try:
                        return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except Exception:
                pass
        return None

    def _resolve_url(self, href: str, base_url: str = 'https://www.sumo.or.jp') -> str:
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return base_url + href
        else:
            return base_url.rstrip('/') + '/' + href.lstrip('/')

    def _remove_duplicates(self, news_items: List[Dict]) -> List[Dict]:
        seen = set()
        unique_items = []
        
        for item in news_items:
            key = item['title'].lower().strip()
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items

    def _filter_relevant_news(self, news_items: List[Dict]) -> List[Dict]:
        exclude_patterns = [
            'home', 'contact', 'about', 'privacy', 'terms',
            'site map', 'english', 'japanese', 'menu', 'login',
            'subscribe', 'newsletter', 'advertisement', 'cookie'
        ]
        
        filtered_items = []
        for item in news_items:
            title_lower = item['title'].lower()
            if (not any(pattern in title_lower for pattern in exclude_patterns) 
                and 15 < len(item['title']) < 200):
                filtered_items.append(item)
        
        # Sort by date (newest first) and source diversity
        filtered_items.sort(key=lambda x: (x.get('date', ''), x.get('source', '')), reverse=True)
        return filtered_items

    def scrape_article_content(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            content_elements = soup.find_all(['article', 'div', 'section', 'p'], 
                                           class_=re.compile(r'content|main'))
            if not content_elements:
                content_elements = soup.find_all('p')
            
            content = ' '.join(element.get_text(strip=True) for element in content_elements)
            
            return content[:1000]  # Limit content length
            
        except Exception as error:
            print(f'Error scraping article: {error}')
            return ''