from flask import Blueprint, jsonify, request, session
from database.models.user import User, db
from database.models.emergencia import Emergencia
from backend.auth.decorators import requiere_rol
from backend.auth.auth_service import registrar_usuario
from datetime import datetime, date

admin_bp = Blueprint('admin', __name__)


# ── Estadísticas generales ──────────────────────────────────────────────────
@admin_bp.route('/admin/stats', methods=['GET'])
@requiere_rol('admin')
def estadisticas():
    total_usuarios    = User.query.filter(User.rol != 'admin').count()
    total_conductores = User.query.filter_by(rol='conductor', activo=True).count()
    conductores_susp  = User.query.filter_by(rol='conductor', activo=False).count()
    emergencias_pend  = Emergencia.query.filter_by(estado='pendiente').count()
    emergencias_hoy   = Emergencia.query.filter(
        db.func.date(Emergencia.fecha_registro) == date.today()
    ).count()
    atendidas_total   = Emergencia.query.filter_by(estado='atendida').count()
    emergencias_total = Emergencia.query.count()

    return jsonify({
        'total_usuarios':    total_usuarios,
        'total_conductores': total_conductores,
        'conductores_susp':  conductores_susp,
        'emergencias_pend':  emergencias_pend,
        'emergencias_hoy':   emergencias_hoy,
        'atendidas_total':   atendidas_total,
        'emergencias_total': emergencias_total,
    }), 200


# ── Historial de emergencias con filtros ────────────────────────────────────
@admin_bp.route('/admin/emergencias', methods=['GET'])
@requiere_rol('admin')
def historial_emergencias():
    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    estado      = request.args.get('estado')

    query = Emergencia.query

    if fecha_desde:
        query = query.filter(
            Emergencia.fecha_registro >= datetime.strptime(fecha_desde, '%Y-%m-%d')
        )
    if fecha_hasta:
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59)
        query = query.filter(Emergencia.fecha_registro <= hasta)
    if estado:
        query = query.filter_by(estado=estado)

    emergencias = query.order_by(Emergencia.fecha_registro.desc()).all()

    return jsonify([{
        'id':              e.id,
        'nombre_paciente': e.nombre_paciente,
        'edad':            e.edad,
        'descripcion':     e.descripcion,
        'direccion':       e.direccion,
        'prioridad':       e.prioridad,
        'estado':          e.estado,
        'fecha_registro':  e.fecha_registro.strftime('%Y-%m-%d %H:%M'),
    } for e in emergencias]), 200


# ── Stats por conductor ─────────────────────────────────────────────────────
@admin_bp.route('/admin/conductores/stats', methods=['GET'])
@requiere_rol('admin')
def stats_conductores():
    conductores = User.query.filter_by(rol='conductor').all()
    return jsonify([{
        'id':                    c.id,
        'nombre':                c.nombre,
        'email':                 c.email,
        'activo':                c.activo,
        'emergencias_atendidas': 0,  # placeholder hasta implementar conductor_id
    } for c in conductores]), 200


# ── Listar usuarios (sin admins) ────────────────────────────────────────────
@admin_bp.route('/admin/usuarios', methods=['GET'])
@requiere_rol('admin')
def listar_usuarios():
    usuarios = User.query.filter(User.rol != 'admin').order_by(User.id).all()
    return jsonify([{
        'id':     u.id,
        'nombre': u.nombre,
        'email':  u.email,
        'rol':    u.rol,
        'activo': u.activo,
    } for u in usuarios]), 200


# ── Crear usuario ───────────────────────────────────────────────────────────
@admin_bp.route('/admin/usuarios', methods=['POST'])
@requiere_rol('admin')
def crear_usuario():
    data = request.get_json()
    user, error = registrar_usuario(
        data.get('nombre'),
        data.get('email'),
        data.get('password'),
        data.get('rol', 'operador')
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'mensaje': f'Usuario {user.nombre} creado correctamente'}), 201


# ── Eliminar usuario ────────────────────────────────────────────────────────
@admin_bp.route('/admin/usuarios/<int:id>', methods=['DELETE'])
@requiere_rol('admin')
def eliminar_usuario(id):
    if session.get('user_id') == id:
        return jsonify({'error': 'No puedes eliminarte a ti mismo'}), 400
    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({'mensaje': 'Usuario eliminado'}), 200


# ── Suspender usuario ───────────────────────────────────────────────────────
@admin_bp.route('/admin/usuarios/<int:id>/suspender', methods=['PUT'])
@requiere_rol('admin')
def suspender_usuario(id):
    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    usuario.activo = False
    db.session.commit()
    return jsonify({'mensaje': f'{usuario.nombre} suspendido'}), 200


# ── Reactivar usuario ───────────────────────────────────────────────────────
@admin_bp.route('/admin/usuarios/<int:id>/reactivar', methods=['PUT'])
@requiere_rol('admin')
def reactivar_usuario(id):
    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    usuario.activo = True
    db.session.commit()
    return jsonify({'mensaje': f'{usuario.nombre} reactivado'}), 200