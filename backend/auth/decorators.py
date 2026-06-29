from functools import wraps
from flask import session, jsonify, request
from database.models.user import User

def requiere_rol(*roles_permitidos):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Intento 1: sesión Flask (cookie)
            if 'user_id' in session and session.get('rol') in roles_permitidos:
                return f(*args, **kwargs)

            # Intento 2: header X-User-Id enviado por el frontend
            user_id = request.headers.get('X-User-Id')
            if user_id:
                user = db_get_user(int(user_id))
                if user and user.rol in roles_permitidos and user.activo:
                    return f(*args, **kwargs)

            return jsonify({'error': 'No autenticado'}), 401
        return wrapper
    return decorador

def db_get_user(user_id):
    try:
        from database.models.user import User
        return User.query.get(user_id)
    except:
        return None