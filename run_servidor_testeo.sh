#!/bin/bash
# Ejecutar Servidor de Testeo (Python + YOLO)

cd /home/guido/Desktop/PC4concurrentes

# Limpiar puerto 5002 si está en uso
echo "🧹 Limpiando puerto 5002..."
lsof -ti:5002 2>/dev/null | xargs -r kill -9
sleep 0.5

# Ejecutar servidor
echo "🚀 Iniciando Servidor de Testeo..."
python3 src/servidor_testeo/servidor_testeo.py
