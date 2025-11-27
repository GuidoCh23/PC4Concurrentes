#!/bin/bash
# Script para liberar puertos 5000 y 5002 automáticamente

echo "Liberando puertos 5000 y 5002..."

# Matar procesos en esos puertos
lsof -ti:5000,5002 2>/dev/null | xargs -r kill -9

sleep 1

# Verificar
if lsof -i:5000,5002 2>/dev/null; then
    echo "⚠️  Algunos puertos aún están en uso"
else
    echo "✅ Puertos 5000 y 5002 liberados"
fi
