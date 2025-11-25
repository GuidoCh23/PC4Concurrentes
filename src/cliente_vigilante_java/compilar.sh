#!/bin/bash

# Script de compilación rápida para Cliente Vigilante Java

echo "============================================================"
echo "COMPILANDO CLIENTE VIGILANTE JAVA"
echo "============================================================"
echo ""

# Verificar Maven
if ! command -v mvn &> /dev/null; then
    echo "ERROR: Maven no está instalado"
    echo "Instalar con: sudo apt install maven"
    exit 1
fi

# Verificar Java
if ! command -v java &> /dev/null; then
    echo "ERROR: Java no está instalado"
    echo "Instalar con: sudo apt install openjdk-11-jdk"
    exit 1
fi

echo "Maven: $(mvn -version | head -n 1)"
echo "Java: $(java -version 2>&1 | head -n 1)"
echo ""

# Compilar
echo "Compilando con Maven..."
mvn clean package

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✓ COMPILACIÓN EXITOSA"
    echo "============================================================"
    echo ""
    echo "JAR generado en:"
    echo "  target/cliente-vigilante-1.0.0-jar-with-dependencies.jar"
    echo ""
    echo "Para ejecutar:"
    echo "  java -jar target/cliente-vigilante-1.0.0-jar-with-dependencies.jar"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "✗ ERROR EN LA COMPILACIÓN"
    echo "============================================================"
    exit 1
fi
