#!/bin/bash
echo "=== Ejecutando verificaciones del proyecto ==="

echo "Revisando sintaxis de archivos Python..."
find backend/ -name "*.py" -exec python -m py_compile {} \;

echo "Verificando que las carpetas principales existen..."
[ -d "backend" ] && echo "backend/ OK" || echo "backend/ NO ENCONTRADA"
[ -d "frontend" ] && echo "frontend/ OK" || echo "frontend/ NO ENCONTRADA"
[ -d "database" ] && echo "database/ OK" || echo "database/ NO ENCONTRADA"

echo "=== Verificacion completada ==="
