from flask import Blueprint, request, jsonify
from database.models.emergencia import Emergencia, db

emergencias_bp = Blueprint('emergencias', __name__)

# ESTAS ES EL METODO GET PARA OBTENER TODAS LAS EMERGENCIAS REGISTRADAS EN LA BASE DE DATOS
@emergencias_bp.route('/emergencias', methods=['GET'])
def obtener_emergencias():
    emergencias = db.session.execute(db.select(Emergencia).order_by(Emergencia.fecha_registro.desc())).scalars().all()
    resultado = []
    for e in emergencias:
        resultado.append({
            'id': e.id,
            'nombre_paciente': e.nombre_paciente,
            'edad': e.edad,
            'descripcion': e.descripcion,
            'direccion': e.direccion,
            'distrito': e.distrito,
            'provincia': e.provincia,
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
        distrito=datos.get('distrito'),
        provincia=datos.get('provincia'),
        latitud=datos.get('latitud'),
        longitud=datos.get('longitud'),
        prioridad=datos.get('prioridad'),
        estado='pendiente'
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify({'mensaje': 'Emergencia registrada correctamente'}), 201

## ESTE ES EL METODO PUT PARA ACTUALIZAR EL ESTADO DE UNA EMERGENCIA EXISTENTE EN LA BASE DE DATOS

@emergencias_bp.route('/emergencias/<int:emergencia_id>/estado', methods=['PUT'])
def actualizar_estado(emergencia_id):
    emergencia = db.session.get(Emergencia, emergencia_id)
    if not emergencia:
        return jsonify({'error': 'Emergencia no encontrada'}), 404

    datos = request.get_json()
    emergencia.estado = datos.get('estado', emergencia.estado)
    db.session.commit()
    return jsonify({'mensaje': 'Estado actualizado correctamente'}), 200


    ## ESTE ES EL METODO PUT PARA ACTUALIZAR TODA LA EMERGENCIA (EDITAR)
@emergencias_bp.route('/emergencias/<int:emergencia_id>', methods=['PUT'])
def actualizar_emergencia(emergencia_id):
    emergencia = db.session.get(Emergencia, emergencia_id)
    if not emergencia:
        return jsonify({'error': 'Emergencia no encontrada'}), 404

    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'No se enviaron datos'}), 400

    # Actualiza todos los campos con los nuevos datos, o deja los que ya estaban
    emergencia.nombre_paciente = datos.get('nombre_paciente', emergencia.nombre_paciente)
    emergencia.edad = datos.get('edad', emergencia.edad)
    emergencia.descripcion = datos.get('descripcion', emergencia.descripcion)
    emergencia.direccion = datos.get('direccion', emergencia.direccion)
    emergencia.distrito = datos.get('distrito', emergencia.distrito)
    emergencia.provincia = datos.get('provincia', emergencia.provincia)
    emergencia.latitud = datos.get('latitud', emergencia.latitud)
    emergencia.longitud = datos.get('longitud', emergencia.longitud)
    emergencia.prioridad = datos.get('prioridad', emergencia.prioridad)
    emergencia.estado = datos.get('estado', emergencia.estado)
    
    if 'conductor_id' in datos:
        emergencia.conductor_id = datos.get('conductor_id')

    db.session.commit()
    return jsonify({'mensaje': 'Emergencia actualizada correctamente'}), 200

## ESTE ES EL METODO DELETE PARA ELIMINAR UNA EMERGENCIA
@emergencias_bp.route('/emergencias/<int:emergencia_id>', methods=['DELETE'])
def eliminar_emergencia(emergencia_id):
    emergencia = db.session.get(Emergencia, emergencia_id)
    if not emergencia:
        return jsonify({'error': 'Emergencia no encontrada'}), 404

    db.session.delete(emergencia)
    db.session.commit()
    return jsonify({'mensaje': 'Emergencia eliminada correctamente'}), 200