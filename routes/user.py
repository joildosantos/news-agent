from flask import Blueprint, jsonify, request, session
from src.models.user import User, Topic, Source, Recipient, db
from functools import wraps

user_bp = Blueprint('user', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Autenticação
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    
    # Se o usuário atual for admin, permite criar novos usuários
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        if current_user and current_user.is_admin:
            pass # Admin pode criar usuários
        else:
            return jsonify({'error': 'Unauthorized: Only admin can create new users'}), 403
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(username=data['username'])
    user.set_password(data['password'])
    user.api_key_news = data.get('api_key_news', '')
    user.is_admin = data.get('is_admin', False) # Permite definir is_admin ao criar
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful', 'user': user.to_dict()})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@user_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'})

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    data = request.json
    
    user.username = data.get('username', user.username)
    user.api_key_news = data.get('api_key_news', user.api_key_news)
    
    if 'password' in data:
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify(user.to_dict())

# Gerenciamento de tópicos
@user_bp.route('/topics', methods=['GET'])
@login_required
def get_topics():
    user = User.query.get(session['user_id'])
    return jsonify([topic.to_dict() for topic in user.topics])

@user_bp.route('/topics', methods=['POST'])
@login_required
def create_topic():
    data = request.json
    topic = Topic(
        user_id=session['user_id'],
        topic_name=data['topic_name'],
        priority=data.get('priority', 3),
        avoid=data.get('avoid', False)
    )
    db.session.add(topic)
    db.session.commit()
    return jsonify(topic.to_dict()), 201

@user_bp.route('/topics/<int:topic_id>', methods=['PUT'])
@login_required
def update_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id, user_id=session['user_id']).first_or_404()
    data = request.json
    
    topic.topic_name = data.get('topic_name', topic.topic_name)
    topic.priority = data.get('priority', topic.priority)
    topic.avoid = data.get('avoid', topic.avoid)
    
    db.session.commit()
    return jsonify(topic.to_dict())

@user_bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@login_required
def delete_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id, user_id=session['user_id']).first_or_404()
    db.session.delete(topic)
    db.session.commit()
    return '', 204

# Gerenciamento de fontes
@user_bp.route('/sources', methods=['GET'])
@login_required
def get_sources():
    user = User.query.get(session['user_id'])
    return jsonify([source.to_dict() for source in user.sources])

@user_bp.route('/sources', methods=['POST'])
@login_required
def create_source():
    data = request.json
    source = Source(
        user_id=session['user_id'],
        source_name=data['source_name'],
        priority=data.get('priority', 3),
        avoid=data.get('avoid', False)
    )
    db.session.add(source)
    db.session.commit()
    return jsonify(source.to_dict()), 201

@user_bp.route('/sources/<int:source_id>', methods=['PUT'])
@login_required
def update_source(source_id):
    source = Source.query.filter_by(id=source_id, user_id=session['user_id']).first_or_404()
    data = request.json
    
    source.source_name = data.get('source_name', source.source_name)
    source.priority = data.get('priority', source.priority)
    source.avoid = data.get('avoid', source.avoid)
    
    db.session.commit()
    return jsonify(source.to_dict())

@user_bp.route('/sources/<int:source_id>', methods=['DELETE'])
@login_required
def delete_source(source_id):
    source = Source.query.filter_by(id=source_id, user_id=session['user_id']).first_or_404()
    db.session.delete(source)
    db.session.commit()
    return '', 204

# Gerenciamento de destinatários
@user_bp.route('/recipients', methods=['GET'])
@login_required
def get_recipients():
    user = User.query.get(session['user_id'])
    return jsonify([recipient.to_dict() for recipient in user.recipients])

@user_bp.route('/recipients', methods=['POST'])
@login_required
def create_recipient():
    data = request.json
    recipient = Recipient(
        user_id=session['user_id'],
        type=data['type'],
        address=data['address']
    )
    db.session.add(recipient)
    db.session.commit()
    return jsonify(recipient.to_dict()), 201

@user_bp.route('/recipients/<int:recipient_id>', methods=['PUT'])
@login_required
def update_recipient(recipient_id):
    recipient = Recipient.query.filter_by(id=recipient_id, user_id=session['user_id']).first_or_404()
    data = request.json
    
    recipient.type = data.get('type', recipient.type)
    recipient.address = data.get('address', recipient.address)
    
    db.session.commit()
    return jsonify(recipient.to_dict())

@user_bp.route('/recipients/<int:recipient_id>', methods=['DELETE'])
@login_required
def delete_recipient(recipient_id):
    recipient = Recipient.query.filter_by(id=recipient_id, user_id=session['user_id']).first_or_404()
    db.session.delete(recipient)
    db.session.commit()
    return '', 204
