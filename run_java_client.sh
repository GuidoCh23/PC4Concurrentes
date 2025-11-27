#!/bin/bash
# Ejecutar Cliente Vigilante en Java

cd /home/guido/Desktop/PC4concurrentes

echo "🚀 Iniciando Cliente Vigilante (Java)"
echo "   Directorio: $(pwd)"
echo "   Config: config/config.json"
echo ""

java -cp src/cliente_vigilante_java/build:src/cliente_vigilante_java/lib/json-20231013.jar \
     com.sistema.vigilante.ClienteVigilante
