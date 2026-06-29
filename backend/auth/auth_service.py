from werkzeug.security import generate_password_hash, check_password_hash
from database.models.user import User, db
import re

# Admin no aparece como rol seleccionable; solo se crea vía SQL
ROLES_VALIDOS = ['operador', 'conductor']

def validar_email(email):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return re.match(patron, email)

def registrar_usuario(nombre, email, password, rol='operador'):
    if not nombre or len(nombre.strip()) < 3:
        return None, "El nombre debe tener al menos 3 caracteres"
    if not email or not validar_email(email):
        return None, "El correo electrónico no es válido"
    if not password or len(password) < 6:
        return None, "La contraseña debe tener al menos 6 caracteres"
    if rol not in ROLES_VALIDOS:
        return None, "Rol inválido. Solo se permite: operador o conductor"
    if User.query.filter_by(email=email).first():
        return None, "El email ya está registrado"

    hash_pw = generate_password_hash(password)
    nuevo = User(
        nombre=nombre.strip(),
        email=email.lower(),
        password_hash=hash_pw,
        rol=rol,
        activo=True
    )
    db.session.add(nuevo)
    db.session.commit()
    return nuevo, None

def verificar_login(email, password):
    if not email or not password:
        return None, "Completa todos los campos"
    if not validar_email(email):
        return None, "El correo electrónico no es válido"
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return None, "Email no encontrado"
    if not check_password_hash(user.password_hash, password):
        return None, "Contraseña incorrecta"
    if not user.activo:
        return None, "Tu cuenta está suspendida. Contacta al administrador."
    return user, None