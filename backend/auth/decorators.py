from functools import wraps
from flask import session, jsonify

def requiere_rol(*roles_permitidos):
    """
    Uso: @requiere_rol('admin') o @requiere_rol('admin', 'operador')
    """
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'No autenticado'}), 401
            if session.get('rol') not in roles_permitidos:
                return jsonify({'error': 'Acceso denegado'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorador