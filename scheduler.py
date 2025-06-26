import schedule
import time
import threading
from datetime import datetime
import os
import sys

# Adiciona o diretório pai ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import User, db
from src.news_service import NewsSearcher, NewsCurator
from src.messaging_service import MessageDispatcher
from flask import Flask

class NewsAgentScheduler:
    def __init__(self, app=None):
        self.app = app
        self.is_running = False
        self.scheduler_thread = None
        
    def init_app(self, app):
        self.app = app
        
    def run_daily_digest_for_all_users(self):
        """
        Executa o resumo diário para todos os usuários configurados
        """
        if not self.app:
            print("Erro: App Flask não configurado")
            return
            
        with self.app.app_context():
            try:
                print(f"[{datetime.now()}] Iniciando execução do resumo diário para todos os usuários")
                
                # Busca todos os usuários que têm configuração completa
                users = User.query.filter(
                    User.api_key_news.isnot(None),
                    User.api_key_news != ''
                ).all()
                
                if not users:
                    print("Nenhum usuário com configuração completa encontrado")
                    return
                
                total_processed = 0
                total_success = 0
                total_failed = 0
                
                for user in users:
                    try:
                        # Verifica se o usuário tem tópicos e destinatários
                        topics = [t.topic_name for t in user.topics if not t.avoid]
                        if not topics or not user.recipients:
                            print(f"Usuário {user.username} não tem configuração completa, pulando...")
                            continue
                        
                        print(f"Processando usuário: {user.username}")
                        result = self.process_user_digest(user)
                        
                        if result['success']:
                            total_success += 1
                            print(f"✓ Sucesso para {user.username}: {result['messages_sent']} mensagens enviadas")
                        else:
                            total_failed += 1
                            print(f"✗ Falha para {user.username}: {result['error']}")
                            
                        total_processed += 1
                        
                    except Exception as e:
                        total_failed += 1
                        print(f"✗ Erro ao processar usuário {user.username}: {str(e)}")
                
                print(f"[{datetime.now()}] Resumo da execução:")
                print(f"  - Usuários processados: {total_processed}")
                print(f"  - Sucessos: {total_success}")
                print(f"  - Falhas: {total_failed}")
                
            except Exception as e:
                print(f"Erro geral na execução do resumo diário: {str(e)}")
    
    def process_user_digest(self, user):
        """
        Processa o resumo diário para um usuário específico
        """
        try:
            # Obtém configurações do usuário
            topics = [t.topic_name for t in user.topics if not t.avoid]
            avoid_topics = [t.topic_name for t in user.topics if t.avoid]
            preferred_sources = [s.source_name for s in user.sources if not s.avoid]
            avoid_sources = [s.source_name for s in user.sources if s.avoid]
            
            if not topics:
                return {'success': False, 'error': 'Nenhum tópico de interesse configurado'}
            
            if not user.recipients:
                return {'success': False, 'error': 'Nenhum destinatário configurado'}
            
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
                return {'success': True, 'messages_sent': 0, 'message': 'Nenhuma notícia relevante encontrada'}
            
            # Gera resumos (limita a 15 artigos)
            summaries = []
            for article in filtered_articles[:15]:
                summary = curator.generate_summary(article)
                summaries.append(summary)
            
            # Envia mensagens
            recipients = [r.to_dict() for r in user.recipients]
            dispatcher = MessageDispatcher()
            result = dispatcher.send_news_digest(recipients, summaries)
            
            return {
                'success': True,
                'total_articles_found': len(articles),
                'total_articles_filtered': len(filtered_articles),
                'total_articles_sent': len(summaries),
                'messages_sent': result['success'],
                'messages_failed': result['failed']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def start_scheduler(self, daily_time="08:00"):
        """
        Inicia o agendador para executar diariamente no horário especificado
        """
        if self.is_running:
            print("Agendador já está em execução")
            return
        
        # Agenda a execução diária
        schedule.clear()
        schedule.every().day.at(daily_time).do(self.run_daily_digest_for_all_users)
        
        print(f"Agendador configurado para executar diariamente às {daily_time}")
        
        self.is_running = True
        
        # Executa o agendador em uma thread separada
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("Agendador iniciado com sucesso")
    
    def stop_scheduler(self):
        """
        Para o agendador
        """
        self.is_running = False
        schedule.clear()
        print("Agendador parado")
    
    def get_status(self):
        """
        Retorna o status do agendador
        """
        next_run = None
        if schedule.jobs:
            next_run = schedule.next_run()
        
        return {
            'is_running': self.is_running,
            'next_run': next_run.isoformat() if next_run else None,
            'jobs_count': len(schedule.jobs)
        }

# Instância global do agendador
scheduler = NewsAgentScheduler()

def create_scheduler_app():
    """
    Cria uma aplicação Flask mínima para o agendador
    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    scheduler.init_app(app)
    
    return app

if __name__ == "__main__":
    # Execução standalone do agendador
    app = create_scheduler_app()
    
    with app.app_context():
        # Inicia o agendador
        scheduler.start_scheduler("08:00")  # 8:00 AM
        
        print("Agendador de notícias iniciado!")
        print("Pressione Ctrl+C para parar")
        
        try:
            # Mantém o programa rodando
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nParando agendador...")
            scheduler.stop_scheduler()
            print("Agendador parado com sucesso!")

