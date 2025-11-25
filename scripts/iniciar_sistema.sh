#!/bin/bash

# Script para iniciar el sistema completo en terminales separadas
# Uso: ./scripts/iniciar_sistema.sh

echo "================================================"
echo "INICIANDO SISTEMA DISTRIBUIDO"
echo "================================================"
echo ""

# Verificar que estamos en la raíz del proyecto
if [ ! -f "config/config.json" ]; then
    echo "ERROR: Ejecutar desde la raíz del proyecto"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado"
    exit 1
fi

# Verificar dependencias
echo "Verificando dependencias..."
python3 -c "import cv2, torch, ultralytics" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ADVERTENCIA: Faltan dependencias. Instalar con:"
    echo "  pip install -r requirements.txt"
    read -p "¿Desea continuar de todas formas? (s/n): " respuesta
    if [ "$respuesta" != "s" ]; then
        exit 1
    fi
fi

echo ""
echo "Iniciando componentes del sistema..."
echo ""

# Función para iniciar en terminal nueva
iniciar_en_terminal() {
    local titulo=$1
    local comando=$2

    # Detectar terminal disponible
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$titulo" -- bash -c "$comando; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -T "$titulo" -e "$comando; bash" &
    elif command -v konsole &> /dev/null; then
        konsole --title "$titulo" -e bash -c "$comando; exec bash" &
    else
        echo "ADVERTENCIA: No se encontró emulador de terminal"
        echo "Ejecutar manualmente: $comando"
    fi
}

# 1. Servidor de Video
echo "[1/3] Iniciando Servidor de Video..."
iniciar_en_terminal "Servidor Video" "python3 src/servidor_video/servidor_video.py"
sleep 2

# 2. Servidor de Testeo
echo "[2/3] Iniciando Servidor de Testeo..."
iniciar_en_terminal "Servidor Testeo" "python3 src/servidor_testeo/servidor_testeo.py"
sleep 2

# 3. Cliente Vigilante
echo "[3/3] Iniciando Cliente Vigilante..."
iniciar_en_terminal "Cliente Vigilante" "python3 src/cliente_vigilante/cliente_vigilante.py"

echo ""
echo "================================================"
echo "✓ Sistema iniciado"
echo "================================================"
echo ""
echo "COMPONENTES:"
echo "  - Servidor Video:     puerto 5000"
echo "  - Servidor Testeo:    puerto 5002"
echo "  - Cliente Vigilante:  GUI"
echo ""
echo "Para detener: Ctrl+C en cada terminal"
echo ""
