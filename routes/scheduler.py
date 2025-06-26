from flask import Blueprint, jsonify, request, session
from src.scheduler import scheduler
from functools import wraps

scheduler_bp = Blueprint('scheduler', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@scheduler_bp.route('/scheduler/status', methods=['GET'])
@login_required
def get_scheduler_status():
    """
    Retorna o status atual do agendador
    """
    try:
        status = scheduler.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'Erro ao obter status: {str(e)}'}), 500

@scheduler_bp.route('/scheduler/start', methods=['POST'])
@login_required
def start_scheduler():
    """
    Inicia o agendador
    """
    try:
        data = request.json or {}
        daily_time = data.get('daily_time', '08:00')
        
        # Valida o formato do horário
        try:
            hour, minute = daily_time.split(':')
            hour = int(hour)
            minute = int(minute)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except:
            return jsonify({'error': 'Formato de horário inválido. Use HH:MM'}), 400
        
        scheduler.start_scheduler(daily_time)
        
        return jsonify({
            'message': f'Agendador iniciado com sucesso para executar diariamente às {daily_time}',
            'daily_time': daily_time
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao iniciar agendador: {str(e)}'}), 500

@scheduler_bp.route('/scheduler/stop', methods=['POST'])
@login_required
def stop_scheduler():
    """
    Para o agendador
    """
    try:
        scheduler.stop_scheduler()
        return jsonify({'message': 'Agendador parado com sucesso'})
    except Exception as e:
        return jsonify({'error': f'Erro ao parar agendador: {str(e)}'}), 500

@scheduler_bp.route('/scheduler/run-now', methods=['POST'])
@login_required
def run_scheduler_now():
    """
    Executa o resumo diário imediatamente para todos os usuários
    """
    try:
        # Executa em uma thread separada para não bloquear a resposta
        import threading
        
        def run_digest():
            scheduler.run_daily_digest_for_all_users()
        
        thread = threading.Thread(target=run_digest)
        thread.start()
        
        return jsonify({'message': 'Execução do resumo diário iniciada para todos os usuários'})
        
    except Exception as e:
        return jsonify({'error': f'Erro ao executar resumo: {str(e)}'}), 500

