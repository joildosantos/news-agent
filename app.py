import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from models.user import db, User
from routes.user import user_bp
from routes.news import news_bp
from routes.scheduler import scheduler_bp
from scheduler import scheduler

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    
    # Habilita CORS para todas as rotas
    CORS(app, supports_credentials=True)
    
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(news_bp, url_prefix='/api')
    app.register_blueprint(scheduler_bp, url_prefix='/api')
    
    # Configuração do banco de dados
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    # Inicializa o agendador
    scheduler.init_app(app)
    
    with app.app_context():
        db.create_all()
        # Cria o usuário admin se ele não existir
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", is_admin=True)
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário admin criado com sucesso!")
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
                return "Static folder not configured", 404
    
        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)