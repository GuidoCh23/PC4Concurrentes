#!/bin/bash
# Ejecutar Servidor de Video (C++)

cd /home/guido/Desktop/PC4concurrentes

# Limpiar puerto 5000 si está en uso
echo "🧹 Limpiando puerto 5000..."
lsof -ti:5000 2>/dev/null | xargs -r kill -9
sleep 0.5

# Ejecutar servidor C++
echo "🚀 Iniciando Servidor de Video (C++)..."
./src/servidor_video_cpp/servidor_video
