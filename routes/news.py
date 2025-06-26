from flask import Blueprint, jsonify, request, session
from src.models.user import User, Topic, Source, Recipient, db
from src.news_service import NewsSearcher, NewsCurator
from src.messaging_service import MessageDispatcher, WhatsAppSender, EmailSender
from functools import wraps
import os

news_bp = Blueprint('news', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@news_bp.route('/test-news-search', methods=['POST'])
@login_required
def test_news_search():
    """
    Testa a busca de notícias com as configurações do usuário
    """
    user = User.query.get(session['user_id'])
    
    if not user.api_key_news:
        return jsonify({'error': 'API key de notícias não configurada'}), 400
    
    try:
        # Obtém configurações do usuário
        topics = [t.topic_name for t in user.topics if not t.avoid]
        avoid_topics = [t.topic_name for t in user.topics if t.avoid]
        preferred_sources = [s.source_name for s in user.sources if not s.avoid]
        avoid_sources = [s.source_name for s in user.sources if s.avoid]
        
        if not topics:
            return jsonify({'error': 'Nenhum tópico de interesse configurado'}), 400
        
        # Busca notícias
        searcher = NewsSearcher(user.api_key_news)
        articles = searcher.search_news(
            topics=topics,
            sources=preferred_sources if preferred_sources else None,
            avoid_sources=avoid_sources
        )
        
        # Faz curadoria
        curator = NewsCurator()
        topic_priorities = {t.topic_name: t.priority for t in user.topics if not t.avoid}
        
        filtered_articles = curator.filter_and_rank_articles(
            articles=articles,
            topic_priorities=topic_priorities,
            avoid_topics=avoid_topics
        )
        
        # Gera resumos
        summaries = []
        for article in filtered_articles[:10]:  # Limita a 10 artigos
            summary = curator.generate_summary(article)
            summaries.append({
                'summary': summary,
                'score': article.get('relevance_score', 0),
                'matched_topics': article.get('matched_topics', [])
            })
        
        return jsonify({
            'total_found': len(articles),
            'total_filtered': len(filtered_articles),
            'summaries': summaries
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar notícias: {str(e)}'}), 500

@news_bp.route('/send-test-message', methods=['POST'])
@login_required
def send_test_message():
    """
    Envia uma mensagem de teste para verificar configuração do WhatsApp
    """
    data = request.json
    recipient_address = data.get('recipient_address')
    recipient_type = data.get('recipient_type', 'whatsapp')
    
    if not recipient_address:
        return jsonify({'error': 'Endereço do destinatário é obrigatório'}), 400
    
    test_message = "🤖 Esta é uma mensagem de teste do seu agente de notícias!"
    
    try:
        if recipient_type == 'whatsapp':
            whatsapp_sender = WhatsAppSender()
            success = whatsapp_sender.send_message(recipient_address, test_message)
        elif recipient_type == 'email':
            email_sender = EmailSender()
            success = email_sender.send_email(
                recipient_address, 
                "Teste - Agente de Notícias", 
                test_message
            )
        else:
            return jsonify({'error': 'Tipo de destinatário inválido'}), 400
        
        if success:
            return jsonify({'message': 'Mensagem de teste enviada com sucesso!'})
        else:
            return jsonify({'error': 'Falha ao enviar mensagem de teste'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao enviar mensagem: {str(e)}'}), 500

@news_bp.route('/run-daily-digest', methods=['POST'])
@login_required
def run_daily_digest():
    """
    Executa o processo completo de busca, curadoria e envio de notícias
    """
    user = User.query.get(session['user_id'])
    
    if not user.api_key_news:
        return jsonify({'error': 'API key de notícias não configurada'}), 400
    
    if not user.recipients:
        return jsonify({'error': 'Nenhum destinatário configurado'}), 400
    
    try:
        # Obtém configurações do usuário
        topics = [t.topic_name for t in user.topics if not t.avoid]
        avoid_topics = [t.topic_name for t in user.topics if t.avoid]
        preferred_sources = [s.source_name for s in user.sources if not s.avoid]
        avoid_sources = [s.source_name for s in user.sources if s.avoid]
        
        if not topics:
            return jsonify({'error': 'Nenhum tópico de interesse configurado'}), 400
        
        # Busca notícias
        searcher = NewsSearcher(user.api_key_news)
        articles = searcher.search_news(
            topics=topics,
            sources=preferred_sources if preferred_sources else None,
            avoid_sources=avoid_sources
        )
        
        # Faz curadoria
        curator = NewsCurator()
        topic_priorities = {t.topic_name: t.priority for t in user.topics if not t.avoid}
        
        filtered_articles = curator.filter_and_rank_articles(
            articles=articles,
            topic_priorities=topic_priorities,
            avoid_topics=avoid_topics
        )
        
        if not filtered_articles:
            return jsonify({'message': 'Nenhuma notícia relevante encontrada hoje'})
        
        # Gera resumos (limita a 15 artigos para não sobrecarregar)
        summaries = []
        for article in filtered_articles[:15]:
            summary = curator.generate_summary(article)
            summaries.append(summary)
        
        # Envia mensagens
        recipients = [r.to_dict() for r in user.recipients]
        dispatcher = MessageDispatcher()
        result = dispatcher.send_news_digest(recipients, summaries)
        
        return jsonify({
            'message': 'Resumo diário processado com sucesso!',
            'total_articles_found': len(articles),
            'total_articles_filtered': len(filtered_articles),
            'total_articles_sent': len(summaries),
            'messages_sent': result['success'],
            'messages_failed': result['failed']
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar resumo diário: {str(e)}'}), 500

@news_bp.route('/config-status', methods=['GET'])
@login_required
def get_config_status():
    """
    Retorna o status da configuração do usuário
    """
    user = User.query.get(session['user_id'])
    
    status = {
        'has_news_api_key': bool(user.api_key_news),
        'has_topics': len(user.topics) > 0,
        'has_recipients': len(user.recipients) > 0,
        'topics_count': len([t for t in user.topics if not t.avoid]),
        'avoid_topics_count': len([t for t in user.topics if t.avoid]),
        'sources_count': len([s for s in user.sources if not s.avoid]),
        'avoid_sources_count': len([s for s in user.sources if s.avoid]),
        'whatsapp_recipients': len([r for r in user.recipients if r.type == 'whatsapp']),
        'email_recipients': len([r for r in user.recipients if r.type == 'email']),
        'ready_to_run': bool(user.api_key_news and user.topics and user.recipients)
    }
    
    return jsonify(status)

