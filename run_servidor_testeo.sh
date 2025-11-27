#!/bin/bash
# Ejecutar Servidor de Testeo (Python + YOLO)

# Obtener directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"


# Limpiar puerto 5002 si está en uso
echo "🧹 Limpiando puerto 5002..."
lsof -ti:5002 2>/dev/null | xargs -r kill -9
sleep 0.5

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️ ADVERTENCIA: No se encontró directorio venv"
fi

# Ejecutar servidor
echo "🚀 Iniciando Servidor de Testeo..."
python3 src/servidor_testeo/servidor_testeo.py
