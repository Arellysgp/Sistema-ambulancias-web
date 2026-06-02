#!/bin/bash
echo "=== Configurando Sistema de Ambulancias Web ==="

echo "Instalando dependencias del backend..."
pip install flask flask-socketio python-dotenv

echo "Verificando estructura del proyecto..."
ls -la backend/ frontend/ database/

echo "=== Setup completado. Proyecto listo ==="
