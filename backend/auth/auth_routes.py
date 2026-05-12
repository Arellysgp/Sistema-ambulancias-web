from flask import Blueprint, request, jsonify, session
from .auth_service import registrar_usuario, verificar_login

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    user, error = registrar_usuario(data['nombre'], data['email'], data['password'])
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'mensaje': 'Usuario registrado correctamente'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user, error = verificar_login(data['email'], data['password'])
    if error:
        return jsonify({'error': error}), 401
    session['user_id'] = user.id
    session['rol'] = user.rol
    return jsonify({'mensaje': 'Login exitoso', 'rol': user.rol}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'}), 200