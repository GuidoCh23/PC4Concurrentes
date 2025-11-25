# Guía Rápida de Inicio

Esta guía te ayudará a poner en funcionamiento el sistema en **menos de 10 minutos**.

---

## Paso 1: Instalar Dependencias (2 minutos)

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate en Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

## Paso 2: Configurar Cámaras (3 minutos)

### Opción A: Usar Webcam Local (Más Rápido)

Modificar `src/servidor_video/servidor_video.py` para usar webcam:

```python
# En la clase CapturaCamera, línea ~70
# Cambiar:
self.capture = cv2.VideoCapture(self.rtsp_url)
# Por:
self.capture = cv2.VideoCapture(0)  # 0 = webcam predeterminada
```

### Opción B: Configurar Cámaras RTSP

Editar `config/config.json`:

```json
{
  "camaras": {
    "lista": [
      {
        "id": 1,
        "rtsp_url": "rtsp://usuario:password@192.168.1.100:554/stream1"
      }
    ]
  }
}
```

Probar conexión:
```bash
python scripts/test_cameras.py
```

---

## Paso 3: Descargar Dataset (2 minutos)

```bash
python scripts/download_dataset.py
# Seleccionar opción 1 (COCO128)
```

El dataset se descargará en `data/coco128/`.

---

## Paso 4: Obtener Modelo Base (1 minuto)

Para pruebas rápidas, el sistema usará el modelo pre-entrenado `yolov8n.pt` que se descarga automáticamente la primera vez.

**Opcional:** Si quieres entrenar tu propio modelo:
```bash
# Iniciar servidor de entrenamiento
python src/servidor_entrenamiento/servidor_entrenamiento.py

# En otra terminal, enviar solicitud (ver README para detalles)
```

---

## Paso 5: Iniciar el Sistema (2 minutos)

### Opción A: Script Automático (Linux/Mac)

```bash
./scripts/iniciar_sistema.sh
```

Esto abrirá 3 terminales automáticamente.

### Opción B: Manual (Todas las plataformas)

**Terminal 1 - Servidor de Video:**
```bash
python src/servidor_video/servidor_video.py
```

**Terminal 2 - Servidor de Testeo:**
```bash
python src/servidor_testeo/servidor_testeo.py
```

**Terminal 3 - Cliente Vigilante:**
```bash
python src/cliente_vigilante/cliente_vigilante.py
```

---

## ¡Listo!

Deberías ver:
- Terminal 1: Capturando frames de las cámaras
- Terminal 2: Procesando y detectando objetos
- Terminal 3: Interfaz gráfica mostrando detecciones

---

## Prueba Rápida

1. Coloca objetos frente a la cámara (persona, celular, laptop, etc.)
2. Observa las detecciones en el Cliente Vigilante
3. Las imágenes se guardan en `detecciones/camara_1/`
4. Los logs en `logs/detecciones.json`

---

## Troubleshooting Rápido

### "No se pudo conectar al servidor de video"
- Verificar que el Servidor de Video esté ejecutándose
- Revisar IP en `config/config.json`

### "Modelo no encontrado"
- El sistema usará yolov8n.pt automáticamente
- Se descarga al primer uso

### "No se detecta ningún objeto"
- El modelo base detecta 80 clases de COCO
- Probar con: persona, celular, laptop, botella, libro
- Acercar objetos a la cámara
- Verificar iluminación

### "Error de webcam"
- Verificar que la webcam no esté siendo usada por otra app
- Probar diferentes IDs: `cv2.VideoCapture(1)` o `(2)`

---

## Próximos Pasos

1. **Entrenar modelo custom:** Ver README sección "Entrenar un Modelo"
2. **Agregar más cámaras:** Editar `config/config.json`
3. **Desplegar en cluster:** Ver README sección "Ejecución en Cluster"

---

## Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f logs/detecciones.json

# Ver detecciones guardadas
ls -lh detecciones/camara_1/

# Limpiar detecciones
rm -rf detecciones/*
rm logs/detecciones.json

# Ver uso de puertos
netstat -tulpn | grep LISTEN  # Linux
lsof -i :5000  # Mac

# Detener todos los procesos Python
pkill -f "python.*servidor"
```

---

**¡Disfruta del sistema!** 🎥🤖
