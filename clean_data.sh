#!/bin/bash

# Script para limpiar datos de detecciones y logs

echo "🧹 Limpiando datos del sistema..."

# Directorios a limpiar
LOG_FILE="logs/detecciones.json"
DETECCIONES_DIR="detecciones"

# Limpiar logs
if [ -f "$LOG_FILE" ]; then
    rm "$LOG_FILE"
    echo "✓ Log eliminado: $LOG_FILE"
else
    echo "ℹ️ No se encontró log: $LOG_FILE"
fi

# Limpiar imágenes
if [ -d "$DETECCIONES_DIR" ]; then
    rm -rf "$DETECCIONES_DIR"
    mkdir "$DETECCIONES_DIR"
    echo "✓ Imágenes eliminadas: $DETECCIONES_DIR"
else
    echo "ℹ️ No se encontró directorio de imágenes: $DETECCIONES_DIR"
    mkdir -p "$DETECCIONES_DIR"
fi

echo "✨ Limpieza completada. El sistema iniciará desde cero."
