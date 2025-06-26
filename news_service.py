import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class NewsSearcher:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"
        
    def search_news(self, topics: List[str], sources: List[str] = None, 
                   avoid_sources: List[str] = None, language: str = 'pt',
                   days_back: int = 1) -> List[Dict]:
        """
        Busca notícias baseado nos tópicos e fontes especificados
        """
        if not self.api_key:
            raise ValueError("API key is required for news search")
            
        # Calcula data de início
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        all_articles = []
        
        for topic in topics:
            # Busca por tópico específico
            params = {
                'q': topic,
                'from': from_date,
                'language': language,
                'sortBy': 'publishedAt',
                'apiKey': self.api_key,
                'pageSize': 20
            }
            
            # Adiciona fontes preferenciais se especificadas
            if sources:
                params['sources'] = ','.join(sources)
            
            try:
                response = requests.get(f"{self.base_url}/everything", params=params)
                response.raise_for_status()
                
                data = response.json()
                if data['status'] == 'ok':
                    articles = data.get('articles', [])
                    
                    # Filtra artigos de fontes a serem evitadas
                    if avoid_sources:
                        articles = [
                            article for article in articles
                            if not any(avoid_source.lower() in article.get('source', {}).get('name', '').lower() 
                                     for avoid_source in avoid_sources)
                        ]
                    
                    # Adiciona o tópico de busca aos artigos
                    for article in articles:
                        article['search_topic'] = topic
                    
                    all_articles.extend(articles)
                    
            except requests.RequestException as e:
                print(f"Erro ao buscar notícias para o tópico '{topic}': {e}")
                continue
        
        # Remove duplicatas baseado na URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    def get_top_headlines(self, country: str = 'br', category: str = None) -> List[Dict]:
        """
        Busca manchetes principais do país
        """
        if not self.api_key:
            raise ValueError("API key is required for news search")
            
        params = {
            'country': country,
            'apiKey': self.api_key,
            'pageSize': 20
        }
        
        if category:
            params['category'] = category
            
        try:
            response = requests.get(f"{self.base_url}/top-headlines", params=params)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'ok':
                return data.get('articles', [])
                
        except requests.RequestException as e:
            print(f"Erro ao buscar manchetes: {e}")
            
        return []

class NewsCurator:
    def __init__(self):
        pass
    
    def filter_and_rank_articles(self, articles: List[Dict], 
                                topic_priorities: Dict[str, int],
                                avoid_topics: List[str] = None) -> List[Dict]:
        """
        Filtra e classifica artigos baseado nas prioridades dos tópicos
        """
        if not articles:
            return []
            
        avoid_topics = avoid_topics or []
        filtered_articles = []
        
        for article in articles:
            # Verifica se o artigo contém tópicos a serem evitados
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = article.get('content', '').lower()
            
            # Pula artigos que contenham tópicos a serem evitados
            if any(avoid_topic.lower() in title or 
                   avoid_topic.lower() in description or 
                   avoid_topic.lower() in content 
                   for avoid_topic in avoid_topics):
                continue
            
            # Calcula pontuação baseada na prioridade dos tópicos
            score = 0
            matched_topics = []
            
            for topic, priority in topic_priorities.items():
                if (topic.lower() in title or 
                    topic.lower() in description or 
                    topic.lower() in content):
                    # Prioridade 1 = mais importante (pontuação maior)
                    score += (6 - priority) * 10
                    matched_topics.append(topic)
            
            if score > 0:  # Só inclui artigos que correspondem aos tópicos de interesse
                article['relevance_score'] = score
                article['matched_topics'] = matched_topics
                filtered_articles.append(article)
        
        # Ordena por pontuação de relevância (maior primeiro)
        filtered_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return filtered_articles
    
    def generate_summary(self, article: Dict) -> str:
        """
        Gera um resumo do artigo
        """
        title = article.get('title', 'Sem título')
        description = article.get('description', '')
        url = article.get('url', '')
        source = article.get('source', {}).get('name', 'Fonte desconhecida')
        published_at = article.get('publishedAt', '')
        
        # Formata a data
        if published_at:
            try:
                date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%d/%m/%Y às %H:%M')
            except:
                formatted_date = published_at
        else:
            formatted_date = 'Data não disponível'
        
        summary = f"📰 *{title}*\n\n"
        
        if description:
            summary += f"📝 {description}\n\n"
        
        summary += f"🔗 {url}\n"
        summary += f"📅 {formatted_date}\n"
        summary += f"📺 Fonte: {source}"
        
        return summary

