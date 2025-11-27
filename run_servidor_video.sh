#!/bin/bash
# Ejecutar Servidor de Video (C++)

# Obtener directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"


# Limpiar puerto 5000 si está en uso
echo "🧹 Limpiando puerto 5000..."
lsof -ti:5000 2>/dev/null | xargs -r kill -9
sleep 0.5

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️ ADVERTENCIA: No se encontró directorio venv"
fi

# Ejecutar servidor (Python)
echo "🚀 Iniciando Servidor de Video (Python)..."
python3 src/servidor_video/servidor_video.py
