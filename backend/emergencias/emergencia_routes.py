from flask import Blueprint, request, jsonify
from database.models.emergencia import Emergencia, db

emergencias_bp = Blueprint('emergencias', __name__)

# ESTAS ES EL METODO GET PARA OBTENER TODAS LAS EMERGENCIAS REGISTRADAS EN LA BASE DE DATOS
@emergencias_bp.route('/emergencias', methods=['GET'])
def obtener_emergencias():
    emergencias = Emergencia.query.order_by(Emergencia.fecha_registro.desc()).all()
    resultado = []
    for e in emergencias:
        resultado.append({
            'id': e.id,
            'nombre_paciente': e.nombre_paciente,
            'edad': e.edad,
            'descripcion': e.descripcion,
            'direccion': e.direccion,
            'latitud': e.latitud,
            'longitud': e.longitud,
            'prioridad': e.prioridad,
            'estado': e.estado,
            'fecha_registro': e.fecha_registro.strftime('%Y-%m-%d %H:%M')
        })
    return jsonify(resultado), 200
## ESTE ES EL METODO POST PARA REGISTRAR UNA NUEVA EMERGENCIA EN LA BASE DE DATOS

@emergencias_bp.route('/emergencias', methods=['POST'])
def registrar_emergencia():
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'No se enviaron datos'}), 400

    campos_requeridos = ['nombre_paciente', 'descripcion', 'direccion', 'prioridad']
    for campo in campos_requeridos:
        if not datos.get(campo):
            return jsonify({'error': f'El campo {campo} es requerido'}), 400

    nueva = Emergencia(
        nombre_paciente=datos.get('nombre_paciente'),
        edad=datos.get('edad'),
        descripcion=datos.get('descripcion'),
        direccion=datos.get('direccion'),
        latitud=datos.get('latitud'),
        longitud=datos.get('longitud'),
        prioridad=datos.get('prioridad'),
        estado='pendiente'
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify({'mensaje': 'Emergencia registrada correctamente'}), 201

## ESTE ES EL METODO PUT PARA ACTUALIZAR EL ESTADO DE UNA EMERGENCIA EXISTENTE EN LA BASE DE DATOS

@emergencias_bp.route('/emergencias/<int:id>/estado', methods=['PUT'])
def actualizar_estado(id):
    emergencia = db.session.get(Emergencia, id)
    if not emergencia:
        return jsonify({'error': 'Emergencia no encontrada'}), 404

    datos = request.get_json()
    emergencia.estado = datos.get('estado', emergencia.estado)
    db.session.commit()
    return jsonify({'mensaje': 'Estado actualizado correctamente'}), 200