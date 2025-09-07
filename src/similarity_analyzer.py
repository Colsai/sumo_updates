"""
Similarity Analyzer for Vector Database

Handles similarity search and article relationship detection using vector embeddings.
"""

from typing import List, Dict, Optional, Tuple
from database import NewsDatabase
from ai_processor import AIProcessor
from tag_manager import TagManager


class SimilarityAnalyzer:
    def __init__(self, database: NewsDatabase, ai_processor: AIProcessor):
        self.db = database
        self.ai = ai_processor
        self.tag_manager = TagManager(database)
        
    def process_new_article(self, article: Dict, 
                          similarity_threshold: float = 0.8,
                          check_duplicates: bool = True) -> Dict:
        """
        Process a new article with vector analysis:
        1. Check for semantic duplicates
        2. Generate embeddings
        3. Find similar articles
        4. Extract entities/topics
        5. Analyze relationships
        6. Save to database
        """
        result = {
            'article_id': None,
            'is_duplicate': False,
            'duplicate_of': None,
            'similar_articles': [],
            'relationships': [],
            'entities': [],
            'topics': []
        }
        
        # Step 1: Check for semantic duplicates first
        if check_duplicates:
            duplicate = self.db.check_semantic_duplicate(
                article.get('content', ''), 
                article.get('title', '')
            )
            if duplicate:
                result['is_duplicate'] = True
                result['duplicate_of'] = duplicate
                print(f"Duplicate detected: {article['title']} matches existing article ID {duplicate['id']}")
                return result
        
        # Step 2: Generate embeddings
        print(f"Generating embeddings for: {article['title']}")
        content_text = f"{article['title']} {article.get('content', '')}"
        title_text = article['title']
        
        content_embedding = self.ai.generate_single_embedding(content_text)
        title_embedding = self.ai.generate_single_embedding(title_text)
        
        # Step 3: Find similar articles using content embedding
        similar_articles = []
        if content_embedding:
            similar_articles = self.db.find_similar_articles(
                content_embedding, 
                table_type='content',
                similarity_threshold=similarity_threshold,
                limit=10
            )
            result['similar_articles'] = similar_articles
            print(f"Found {len(similar_articles)} similar articles")
        
        # Step 4: Extract entities and topics
        entities, topics = self.ai.extract_entities_and_topics(
            article.get('content', ''), 
            article.get('title', '')
        )
        result['entities'] = entities
        result['topics'] = topics
        
        # Step 4a: Generate tags for the article
        print(f"Generating tags for: {article['title']}")
        try:
            tags, tag_scores = self.ai.generate_tags_for_article(
                article.get('title', ''),
                article.get('content', ''),
                entities
            )
            result['tags'] = tags
            result['tag_scores'] = tag_scores
            print(f"Generated {len(tags)} tags: {tags[:5]}..." if len(tags) > 5 else f"Generated tags: {tags}")
        except Exception as e:
            print(f"Error generating tags: {e}")
            result['tags'] = []
            result['tag_scores'] = []
        
        # Step 5: Analyze relationships with similar articles
        if similar_articles:
            relationships = self.ai.analyze_article_relationships(
                content_text, 
                similar_articles[:5]
            )
            result['relationships'] = relationships
        
        # Step 6: Save article with embeddings to database
        try:
            article_id = self.db.save_article_with_embeddings(
                article=article,
                content_embedding=content_embedding,
                title_embedding=title_embedding,
                embedding_model='text-embedding-3-small',
                topics=topics,
                entities=entities
            )
            
            if article_id:
                result['article_id'] = article_id
                print(f"Saved article with ID: {article_id}")
                
                # Add tags to the saved article
                if result.get('tags') and article_id:
                    try:
                        added_tags = self.tag_manager.add_tags_to_article(
                            article_id, 
                            result['tags'], 
                            result.get('tag_scores'),
                            'ai-system'
                        )
                        print(f"Added {added_tags} tags to article")
                    except Exception as e:
                        print(f"Error adding tags: {e}")
                
                # Add relationships to database
                for rel in result['relationships']:
                    if rel.get('article_id') and rel.get('confidence', 0) >= 0.6:
                        self.db.add_article_relationship(
                            source_id=article_id,
                            target_id=rel['article_id'],
                            relationship_type=rel['type'],
                            confidence_score=rel['confidence']
                        )
                        print(f"Added {rel['type']} relationship with confidence {rel['confidence']:.2f}")
            
        except Exception as e:
            print(f"Error saving article: {e}")
        
        return result
    
    def find_article_references(self, article_id: int, 
                              relationship_types: List[str] = None) -> List[Dict]:
        """Find all articles that reference or are related to a specific article"""
        if relationship_types is None:
            relationship_types = ['reference', 'update', 'related']
        
        return self.db.get_article_relationships(article_id, relationship_types)
    
    def batch_process_existing_articles(self, limit: int = None) -> Dict:
        """Process existing articles that don't have embeddings"""
        articles = self.db.get_articles_without_embeddings(limit)
        
        results = {
            'processed': 0,
            'errors': 0,
            'new_relationships': 0
        }
        
        print(f"Processing {len(articles)} articles without embeddings...")
        
        for i, article in enumerate(articles):
            try:
                print(f"Processing {i+1}/{len(articles)}: {article['title']}")
                
                # Generate embeddings
                content_text = f"{article['title']} {article.get('content', '')}"
                title_text = article['title']
                
                content_embedding = self.ai.generate_single_embedding(content_text)
                title_embedding = self.ai.generate_single_embedding(title_text)
                
                # Extract entities and topics if not present
                entities, topics = [], []
                if not article.get('entities') or not article.get('topics'):
                    entities, topics = self.ai.extract_entities_and_topics(
                        article.get('content', ''), 
                        article.get('title', '')
                    )
                
                # Update database with embeddings
                self.db.update_article_embeddings(
                    article_id=article['id'],
                    content_embedding=content_embedding,
                    title_embedding=title_embedding
                )
                
                # Find and add relationships with similar articles
                if content_embedding:
                    similar_articles = self.db.find_similar_articles(
                        content_embedding, 
                        similarity_threshold=0.8,
                        limit=5
                    )
                    
                    if similar_articles:
                        relationships = self.ai.analyze_article_relationships(
                            content_text, 
                            similar_articles
                        )
                        
                        for rel in relationships:
                            if rel.get('article_id') and rel.get('confidence', 0) >= 0.7:
                                self.db.add_article_relationship(
                                    source_id=article['id'],
                                    target_id=rel['article_id'],
                                    relationship_type=rel['type'],
                                    confidence_score=rel['confidence']
                                )
                                results['new_relationships'] += 1
                
                results['processed'] += 1
                
                # Rate limiting
                import time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing article {article.get('id')}: {e}")
                results['errors'] += 1
        
        return results
    
    def get_article_context(self, article_id: int) -> Dict:
        """Get full context for an article including relationships and similar articles"""
        # Get the main article
        with self.db._get_connection() as conn:
            conn.row_factory = self.db.sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM news_articles WHERE id = ?', (article_id,))
            article = cursor.fetchone()
            
            if not article:
                return {}
        
        article_dict = dict(article)
        
        # Get relationships
        relationships = self.db.get_article_relationships(article_id)
        
        # If article has embeddings, find similar articles
        similar_articles = []
        if article_dict.get('content_embedding'):
            embedding = self.db._deserialize_embedding(article_dict['content_embedding'])
            similar_articles = self.db.find_similar_articles(
                embedding, 
                similarity_threshold=0.7,
                limit=10
            )
        
        return {
            'article': article_dict,
            'relationships': relationships,
            'similar_articles': similar_articles,
            'entities': article_dict.get('entities'),
            'topics': article_dict.get('topics')
        }