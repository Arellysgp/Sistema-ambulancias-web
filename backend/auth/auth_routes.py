from flask import Blueprint, request, jsonify, session
from .auth_service import registrar_usuario, verificar_login

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    print("DEBUG REGISTER DATA:", data)
    rol = data.get('rol', 'operador')
    nombre = data.get('nombre', '')
    email = data.get('email', '')
    try:
        data = request.get_json()
        
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')
        rol = data.get('rol', 'operador') # por defecto operador

        if not all([nombre, email, password]):
            return jsonify({'error': 'Faltan datos obligatorios'}), 400

        user, error = registrar_usuario(nombre, email, password, rol)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': user.id,
                'nombre': user.nombre,
                'email': user.email,
                'rol': user.rol
            }
        }), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'SERVER EXCEPTION: ' + str(e), 'trace': traceback.format_exc()}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    print("DEBUG LOGIN DATA:", data)
    email = data.get('email', '')
    password = data.get('password', '')
    user, error = verificar_login(email, password)
    if error:
        return jsonify({'error': error}), 401
    session.permanent = True
    session['user_id'] = user.id
    session['rol']     = user.rol
    session['nombre']  = user.nombre
    return jsonify({
        'mensaje': 'Login exitoso',
        'rol':     user.rol,
        'nombre':  user.nombre,
        'user_id': user.id        # ← enviamos el id al frontend
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'}), 200