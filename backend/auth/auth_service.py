from werkzeug.security import generate_password_hash, check_password_hash
from database.models.user import User, db

def registrar_usuario(nombre, email, password):
    if User.query.filter_by(email=email).first():
        return None, "El email ya está registrado"
    hash_pw = generate_password_hash(password)
    nuevo = User(nombre=nombre, email=email, password_hash=hash_pw)
    db.session.add(nuevo)
    db.session.commit()
    return nuevo, None

def verificar_login(email, password):
    user = User.query.filter_by(email=email).first()
    if not user:
        return None, "Email no encontrado"
    if not check_password_hash(user.password_hash, password):
        return None, "Contraseña incorrecta"
    return user, None