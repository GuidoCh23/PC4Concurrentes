#!/bin/bash
# Ejecutar Cliente Vigilante en Java

# Obtener directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"


echo "🚀 Iniciando Cliente Vigilante (Java)"
echo "   Directorio: $(pwd)"
echo "   Config: config/config.json"
echo ""

# Ejecutar JAR compilado
java -jar src/cliente_vigilante_java/target/cliente-vigilante-1.0.0-jar-with-dependencies.jar config/config.json
