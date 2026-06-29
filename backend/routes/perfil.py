# backend/routes/perfil.py
# Rutas de perfil de usuario — Sistema SAMU
# Compatible con el sistema de autenticación existente (X-User-Id + session)

from flask import Blueprint, jsonify, request, session
from database.models.user import db
from database.models.user import User as Usuario
import base64, re, uuid, os

try:
    import requests as req_lib
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

perfil_bp = Blueprint('perfil', __name__)

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
BUCKET       = 'avatares'


def _get_user_id():
    uid = session.get('user_id') or request.headers.get('X-User-Id')
    try:
        return int(uid) if uid else None
    except (ValueError, TypeError):
        return None


def _require_auth():
    if not _get_user_id():
        return jsonify({'error': 'No autorizado'}), 401
    return None


def _upload_supabase(b64: str) -> str | None:
    """Sube imagen base64 al bucket de Supabase y devuelve URL pública."""
    if not SUPABASE_URL or not SUPABASE_KEY or not REQUESTS_OK:
        return None
    m = re.match(r'data:(image/\w+);base64,(.+)', b64)
    if not m:
        return None
    mime = m.group(1)
    raw  = base64.b64decode(m.group(2))
    ext  = mime.split('/')[1]
    name = f'{uuid.uuid4().hex}.{ext}'
    url  = f'{SUPABASE_URL}/storage/v1/object/{BUCKET}/{name}'
    hdrs = {'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': mime, 'x-upsert': 'true'}
    r = req_lib.post(url, headers=hdrs, data=raw, timeout=15)
    if r.status_code not in (200, 201):
        return None
    return f'{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{name}'


#  GET /api/perfil — datos del usuario logueado

@perfil_bp.route('/api/perfil', methods=['GET'])
def obtener_perfil():
    err = _require_auth()
    if err: return err
    u = Usuario.query.get(_get_user_id())
    if not u:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    return jsonify({
        'id':             u.id,
        'nombre':         u.nombre,
        'apellido':       getattr(u, 'apellido', '') or '',
        'email':          u.email,
        'rol':            u.rol,
        'telefono':       getattr(u, 'telefono', '') or '',
        'foto_url':       getattr(u, 'foto_url', '') or '',
        'activo':         u.activo,
        'fecha_registro': u.fecha_registro.isoformat() if getattr(u,'fecha_registro',None) else None,
    })


#  PUT /api/perfil — actualizar datos + foto

@perfil_bp.route('/api/perfil', methods=['PUT'])
def actualizar_perfil():
    err = _require_auth()
    if err: return err
    u    = Usuario.query.get(_get_user_id())
    if not u:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    data = request.get_json(silent=True) or {}

    if 'nombre'   in data: u.nombre   = data['nombre'].strip()
    if 'apellido' in data:
        if hasattr(u, 'apellido'): u.apellido = data['apellido'].strip()
    if 'telefono' in data:
        if hasattr(u, 'telefono'): u.telefono = data['telefono'].strip()

    foto_url = None
    if data.get('foto_base64'):
        # Intenta subir a Supabase; si no hay config, guarda base64 directo
        url = _upload_supabase(data['foto_base64'])
        foto_url = url or data['foto_base64']
        if hasattr(u, 'foto_url'): u.foto_url = foto_url

    db.session.commit()
    return jsonify({'ok': True, 'foto_url': foto_url or getattr(u,'foto_url','')})


#  PUT /api/perfil/password — cambiar contraseña

@perfil_bp.route('/api/perfil/password', methods=['PUT'])
def cambiar_password():
    err = _require_auth()
    if err: return err
    from werkzeug.security import check_password_hash, generate_password_hash
    u    = Usuario.query.get(_get_user_id())
    data = request.get_json(silent=True) or {}
    actual   = data.get('password_actual', '')
    nueva    = data.get('password_nueva', '')
    confirma = data.get('password_confirma', '')

    if not check_password_hash(u.password, actual):   # ajusta el campo si se llama distinto
        return jsonify({'error': 'Contraseña actual incorrecta'}), 400
    if len(nueva) < 6:
        return jsonify({'error': 'Mínimo 6 caracteres'}), 400
    if nueva != confirma:
        return jsonify({'error': 'Las contraseñas no coinciden'}), 400

    u.password = generate_password_hash(nueva)
    db.session.commit()
    return jsonify({'ok': True})
