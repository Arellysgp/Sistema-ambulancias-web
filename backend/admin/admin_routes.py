from flask import Blueprint, jsonify, request, session
from database.models.user import User, db
from database.models.emergencia import Emergencia
from backend.auth.decorators import requiere_rol
from backend.auth.auth_service import registrar_usuario
from datetime import datetime, date

admin_bp = Blueprint('admin', __name__)

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


@admin_bp.route('/admin/emergencias', methods=['GET'])
@requiere_rol('admin')
def historial_emergencias():
    estado = request.args.get('estado')
    prioridad = request.args.get('prioridad')
    fecha_ini = request.args.get('fecha_ini')
    fecha_fin = request.args.get('fecha_fin')
    
    query  = Emergencia.query
    if estado:
        query = query.filter_by(estado=estado)
    if prioridad:
        query = query.filter_by(prioridad=int(prioridad))
    if fecha_ini:
        query = query.filter(Emergencia.fecha_registro >= datetime.fromisoformat(fecha_ini))
    if fecha_fin:
        fecha_fin_dt = datetime.fromisoformat(fecha_fin).replace(hour=23, minute=59, second=59)
        query = query.filter(Emergencia.fecha_registro <= fecha_fin_dt)
        
    emergencias = query.order_by(Emergencia.fecha_registro.desc()).all()

    def fmt_fecha(e):
        if not e.fecha_registro:
            return 'Sin fecha'
        return e.fecha_registro.strftime('%Y-%m-%d %H:%M')

    return jsonify([{
        'id':              e.id,
        'nombre_paciente': e.nombre_paciente,
        'edad':            e.edad,
        'descripcion':     e.descripcion,
        'direccion':       e.direccion,
        'prioridad':       e.prioridad,
        'estado':          e.estado,
        'fecha_registro':  fmt_fecha(e),
    } for e in emergencias]), 200


@admin_bp.route('/admin/conductores/stats', methods=['GET'])
@requiere_rol('admin')
def stats_conductores():
    conductores = User.query.filter_by(rol='conductor').all()
    return jsonify([{
        'id':                    c.id,
        'nombre':                c.nombre,
        'email':                 c.email,
        'activo':                c.activo,
        'emergencias_atendidas': Emergencia.query.filter_by(conductor_id=c.id, estado='atendida').count(),
    } for c in conductores]), 200


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


@admin_bp.route('/admin/usuarios/<int:id>', methods=['GET'])
@requiere_rol('admin')
def obtener_usuario(id):
    u = db.session.get(User, id)
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
    }), 200


@admin_bp.route('/admin/usuarios', methods=['POST'])
@requiere_rol('admin')
def crear_usuario():
    data = request.get_json()
    user, error = registrar_usuario(
        data.get('nombre'), data.get('email'),
        data.get('password'), data.get('rol', 'operador')
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'mensaje': f'Usuario {user.nombre} creado correctamente'}), 201


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


@admin_bp.route('/admin/usuarios/<int:id>/suspender', methods=['PUT'])
@requiere_rol('admin')
def suspender_usuario(id):
    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    usuario.activo = False
    db.session.commit()
    return jsonify({'mensaje': f'{usuario.nombre} suspendido'}), 200


@admin_bp.route('/admin/usuarios/<int:id>/reactivar', methods=['PUT'])
@requiere_rol('admin')
def reactivar_usuario(id):
    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    usuario.activo = True
    db.session.commit()
    return jsonify({'mensaje': f'{usuario.nombre} reactivado'}), 200

import math
from database.models.emergencia import Emergencia

# Fórmula matemática de Haversine para calcular distancias en km
def calcular_distancia(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 9999.0 # Si no tiene GPS, lo mandamos al final
        
    R = 6371.0  # Radio de la Tierra en kilómetros
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

@admin_bp.route('/admin/recomendacion/<int:emergencia_id>', methods=['GET'])
@requiere_rol('admin')
def recomendar_conductor(emergencia_id):
    emergencia = Emergencia.query.get_or_404(emergencia_id)
    
    # Obtenemos solo a los conductores que están activos
    conductores = User.query.filter_by(rol='conductor', activo=True).all()
    
    resultados = []
    for c in conductores:
        # Por ahora, si un conductor no tiene GPS real en la DB, le simularemos 
        # uno temporal cerca de Lima para que el algoritmo siempre funcione en tu presentación.
        # (Centro de Lima: -12.0463, -77.0427)
        c_lat = c.latitud if c.latitud else -12.0463 + (c.id * 0.01)
        c_lon = c.longitud if c.longitud else -77.0427 + (c.id * 0.01)
        
        distancia = calcular_distancia(emergencia.latitud, emergencia.longitud, c_lat, c_lon)
        resultados.append({
            'id': c.id,
            'nombre': c.nombre,
            'distancia_km': distancia
        })
    
    # Ordenamos de menor a mayor distancia
    resultados_ordenados = sorted(resultados, key=lambda x: x['distancia_km'])
    
    return jsonify(resultados_ordenados), 200

@admin_bp.route('/admin/emergencias/<int:emergencia_id>/asignar', methods=['PUT'])
@requiere_rol('admin')
def asignar_emergencia_admin(emergencia_id):
    emergencia = Emergencia.query.get_or_404(emergencia_id)
    data = request.json
    conductor_id = data.get('conductor_id')
    
    if not conductor_id:
        return jsonify({'error': 'Falta conductor_id'}), 400
        
    conductor = User.query.get(conductor_id)
    if not conductor or conductor.rol != 'conductor':
        return jsonify({'error': 'Conductor inválido'}), 400
        
    # Asignamos al conductor
    emergencia.conductor_id = conductor_id
    db.session.commit()
    
    return jsonify({'mensaje': f'Ambulancia de {conductor.nombre} asignada correctamente'}), 200

