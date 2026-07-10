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
    password = data.get('password', '')
    user, error = registrar_usuario(nombre, email, password, rol)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'mensaje': 'Usuario registrado correctamente'}), 201

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