# Sistema Distribuido de Reconocimiento de Objetos con IA

**Práctica 04 - CC4P1 Programación Concurrente y Distribuida**

Sistema distribuido para el entrenamiento y detección de objetos en tiempo real utilizando YOLO v8 y múltiples cámaras IP (RTSP).

---

## Características Principales

- **Arquitectura Distribuida:** 3 servidores + 1 cliente comunicados mediante sockets puros TCP
- **Detección en Tiempo Real:** Procesamiento de video desde múltiples cámaras simultáneamente
- **Modelo de IA:** YOLOv8 para reconocimiento de objetos
- **Concurrencia:** Uso de hilos (threads) para procesamiento paralelo
- **Protocolo Custom:** Comunicación mediante protocolo propio sin frameworks
- **Persistencia:** Almacenamiento de modelos entrenados y logs de detecciones
- **Interfaz Gráfica:** Cliente vigilante con Tkinter para monitoreo en tiempo real

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  Cámaras RTSP  →  SERVIDOR VIDEO  →  SERVIDOR TESTEO        │
│    (1...C)         (Puerto 5000)      (Puerto 5002)          │
│                                              ↓                │
│                                     [Detecciones]            │
│                                              ↓                │
│                                    CLIENTE VIGILANTE         │
│                                        (Tkinter UI)          │
│                                                               │
│                    SERVIDOR ENTRENAMIENTO                    │
│                       (Puerto 5001)                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

1. **Servidor de Video** (`src/servidor_video/`)
   - Captura video desde C cámaras IP (RTSP)
   - Usa hilos para captura simultánea
   - Envía frames a servidor de testeo vía sockets TCP

2. **Servidor de Entrenamiento** (`src/servidor_entrenamiento/`)
   - Entrena modelos YOLO con datasets custom
   - Guarda modelos entrenados persistentemente
   - Responde a solicitudes de entrenamiento

3. **Servidor de Testeo** (`src/servidor_testeo/`)
   - Recibe frames del servidor de video
   - Aplica modelo YOLO para detectar objetos
   - Guarda imágenes y logs de detecciones
   - Notifica al cliente vigilante

4. **Cliente Vigilante** (`src/cliente_vigilante/`)
   - Interfaz gráfica (Tkinter)
   - Visualiza detecciones en tiempo real
   - Muestra historial con imágenes

---

## Requisitos del Sistema

### Software
- Python 3.8+
- OpenCV
- PyTorch
- Ultralytics YOLOv8
- Pillow (para GUI)
- Tkinter (generalmente incluido con Python)

### Hardware
- **Mínimo:** CPU multi-core, 8GB RAM
- **Recomendado:** GPU NVIDIA con CUDA, 16GB RAM

### Red
- Conexión LAN o WiFi
- Acceso a cámaras IP con protocolo RTSP
- Puertos 5000-5002 disponibles

---

## Instalación

### 1. Clonar/Descargar el Proyecto

```bash
cd PC4concurrentes
```

### 2. Crear Entorno Virtual (Recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Nota:** La instalación de PyTorch puede requerir comandos específicos según tu sistema.
Visita: https://pytorch.org/get-started/locally/

---

## Configuración

### 1. Configurar Cámaras RTSP

Editar `config/config.json` y completar las URLs de las cámaras:

```json
{
  "camaras": {
    "cantidad": 3,
    "lista": [
      {
        "id": 1,
        "nombre": "Camara Entrada",
        "rtsp_url": "rtsp://usuario:password@192.168.1.100:554/stream1",
        "enabled": true
      },
      {
        "id": 2,
        "nombre": "Camara Pasillo",
        "rtsp_url": "rtsp://usuario:password@192.168.1.101:554/stream1",
        "enabled": true
      }
    ]
  }
}
```

**Formato RTSP:** `rtsp://usuario:password@IP:puerto/stream`

### 2. Configurar IPs de Servidores (Para Cluster)

Si ejecutas en múltiples máquinas, editar `config/config.json`:

```json
{
  "servidor_video": {
    "host": "0.0.0.0",  // Escucha en todas las interfaces
    "puerto": 5000
  },
  "servidor_testeo": {
    "host": "0.0.0.0",
    "puerto": 5002
  },
  "cliente_vigilante": {
    "servidor_testeo_host": "192.168.1.10",  // IP del servidor de testeo
    "servidor_testeo_puerto": 5002
  }
}
```

### 3. Verificar Cámaras

Probar conexión a cámaras:

```bash
python scripts/test_cameras.py
```

---

## Preparación del Dataset

### Opción 1: Dataset COCO128 (Recomendado para Pruebas)

```bash
python scripts/download_dataset.py
# Seleccionar opción 1
```

El dataset COCO128 contiene 80 clases de objetos comunes:
- Personas, vehículos, animales, objetos cotidianos

### Opción 2: Dataset de Kaggle

Configurar Kaggle API:
1. Ir a https://www.kaggle.com/settings/account
2. Crear API token → Descargar `kaggle.json`
3. Colocar en `~/.kaggle/kaggle.json` (Linux/Mac) o `C:\Users\<user>\.kaggle\` (Windows)

Descargar dataset:

```bash
python scripts/download_dataset.py
# Seleccionar opción 2
# Ejemplo: ultralytics/coco128
```

### Opción 3: Dataset Custom

```bash
python scripts/download_dataset.py
# Seleccionar opción 3
# Seguir instrucciones para crear estructura
```

Estructura del dataset:
```
data/mi_dataset/
├── images/
│   ├── train/  <- Imágenes de entrenamiento
│   └── val/    <- Imágenes de validación
├── labels/
│   ├── train/  <- Etiquetas YOLO (.txt)
│   └── val/
└── data.yaml   <- Configuración del dataset
```

---

## Uso del Sistema

### Orden de Ejecución

**IMPORTANTE:** Iniciar en este orden:

#### 1. Servidor de Entrenamiento (Opcional - solo si vas a entrenar)

```bash
python src/servidor_entrenamiento/servidor_entrenamiento.py
```

#### 2. Servidor de Video

```bash
python src/servidor_video/servidor_video.py
```

Debe mostrar:
```
=== Servidor de Video ===
Cámaras configuradas: 3
[Cámara 1] Conexión exitosa
[Cámara 2] Conexión exitosa
[Cámara 3] Conexión exitosa
Servidor escuchando en puerto 5000
```

#### 3. Servidor de Testeo

```bash
python src/servidor_testeo/servidor_testeo.py
```

Debe mostrar:
```
=== Servidor de Testeo/Detección ===
Cargando modelo desde: models/mejor_modelo.pt
Modelo cargado exitosamente
Conectando al servidor de video: 127.0.0.1:5000
Conexión exitosa
```

#### 4. Cliente Vigilante

```bash
python src/cliente_vigilante/cliente_vigilante.py
```

Se abrirá la interfaz gráfica mostrando detecciones en tiempo real.

---

## Entrenar un Modelo

### 1. Preparar Dataset

Asegurarse de tener un dataset en formato YOLO con su `data.yaml`.

### 2. Iniciar Servidor de Entrenamiento

```bash
python src/servidor_entrenamiento/servidor_entrenamiento.py
```

### 3. Enviar Solicitud de Entrenamiento

Crear un script cliente o usar Python interactivo:

```python
import socket
import sys
sys.path.append('.')

from src.common.protocolo import Protocolo, TipoMensaje

# Conectar al servidor
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 5001))

# Enviar solicitud de entrenamiento
Protocolo.enviar_mensaje(sock, TipoMensaje.TRAIN_REQUEST, {
    'dataset_path': 'data/coco128/data.yaml',
    'epochs': 50
})

# Recibir respuesta
mensaje = Protocolo.recibir_mensaje(sock)
print(mensaje)

sock.close()
```

El modelo entrenado se guardará en `models/mejor_modelo.pt`.

---

## Ejecución en Cluster (Múltiples PCs)

### Configuración

**PC 1 - Servidor de Video:**
```json
{
  "servidor_video": {
    "host": "0.0.0.0",  // Escuchar en todas las interfaces
    "puerto": 5000
  }
}
```

**PC 2 - Servidor de Testeo:**
```json
{
  "servidor_testeo": {
    "host": "0.0.0.0",
    "puerto": 5002
  }
}
```

En `servidor_testeo.py`, configurar IP del servidor de video:
```python
self.video_host = "192.168.1.10"  # IP de PC 1
```

**PC 3 - Cliente Vigilante:**
```json
{
  "cliente_vigilante": {
    "servidor_testeo_host": "192.168.1.20",  // IP de PC 2
    "servidor_testeo_puerto": 5002
  }
}
```

### Firewall

Abrir puertos en el firewall:

**Linux:**
```bash
sudo ufw allow 5000/tcp
sudo ufw allow 5001/tcp
sudo ufw allow 5002/tcp
```

**Windows:**
Configuración → Firewall → Reglas de entrada → Nueva regla

---

## Estructura del Proyecto

```
PC4concurrentes/
├── config/
│   └── config.json              # Configuración del sistema
├── data/                        # Datasets
│   ├── train/
│   └── test/
├── models/                      # Modelos entrenados
│   └── mejor_modelo.pt
├── detecciones/                 # Imágenes de detecciones
│   ├── camara_1/
│   ├── camara_2/
│   └── camara_3/
├── logs/
│   └── detecciones.json         # Log de detecciones
├── src/
│   ├── common/                  # Módulos comunes
│   │   ├── protocolo.py         # Protocolo de comunicación
│   │   └── utils.py             # Utilidades
│   ├── servidor_video/          # Servidor de video
│   │   └── servidor_video.py
│   ├── servidor_entrenamiento/  # Servidor de entrenamiento
│   │   └── servidor_entrenamiento.py
│   ├── servidor_testeo/         # Servidor de testeo
│   │   └── servidor_testeo.py
│   └── cliente_vigilante/       # Cliente vigilante
│       └── cliente_vigilante.py
├── scripts/
│   ├── download_dataset.py      # Descarga de datasets
│   └── test_cameras.py          # Prueba de cámaras
├── docs/
│   └── INTERPRETACION_PROYECTO.md
├── requirements.txt
└── README.md
```

---

## Protocolo de Comunicación

### Formato de Mensajes

Todos los mensajes siguen el formato:

```
[4 bytes: tamaño] [N bytes: mensaje JSON]
```

Estructura del mensaje JSON:
```json
{
  "tipo": "FRAME",
  "timestamp": "2025-11-25T14:30:25.123456",
  "datos": {
    "camera_id": 1,
    "frame_data": "<base64_encoded_image>",
    ...
  }
}
```

### Tipos de Mensajes

| Tipo | Descripción |
|------|-------------|
| `FRAME` | Frame de video (Video → Testeo) |
| `DETECTION` | Detección de objeto (Testeo → Vigilante) |
| `TRAIN_REQUEST` | Solicitud de entrenamiento |
| `TRAIN_COMPLETE` | Entrenamiento completado |
| `MODEL_READY` | Modelo listo para usar |
| `GET_DETECTIONS` | Solicitar historial |
| `ACK` | Confirmación |
| `ERROR` | Error |

### Ejemplo: Detección

```json
{
  "tipo": "DETECTION",
  "timestamp": "2025-11-25T14:30:25",
  "datos": {
    "camera_id": 1,
    "objeto": "perro",
    "confianza": 0.95,
    "bbox": [100, 150, 300, 400],
    "imagen_path": "detecciones/camara_1/20251125_143025.jpg",
    "fecha": "2025-11-25",
    "hora": "14:30:25"
  }
}
```

---

## Características Técnicas

### Concurrencia

- **Servidor de Video:** 1 hilo por cámara para captura simultánea
- **Servidor de Testeo:** Pool de hilos para procesamiento paralelo (configurable)
- **Sincronización:** Uso de locks para acceso thread-safe a recursos compartidos

### Persistencia

- **Modelos:** Guardados en formato PyTorch (.pt)
- **Detecciones:** JSON con metadata + imágenes en disco
- **Configuración:** JSON para fácil edición

### Seguridad

- **No incluye autenticación:** Implementar si se despliega en producción
- **RTSP:** Usar credenciales fuertes para cámaras
- **Red:** Ejecutar en red privada/VPN

---

## Solución de Problemas

### Error: No se puede conectar a la cámara

- Verificar URL RTSP
- Probar con VLC: `vlc rtsp://...`
- Verificar credenciales
- Revisar firewall/red

### Error: Modelo no encontrado

- Entrenar modelo primero o usar modelo base:
  ```python
  self.modelo = YOLO('yolov8n.pt')  # Modelo pre-entrenado
  ```

### Error: Puerto en uso

- Cambiar puerto en `config/config.json`
- O cerrar proceso que usa el puerto:
  ```bash
  lsof -i :5000  # Ver proceso
  kill -9 <PID>  # Terminar proceso
  ```

### Bajo FPS / Alto uso de CPU

- Reducir resolución de frames en config
- Reducir FPS de captura
- Usar modelo YOLO más ligero (yolov8n en lugar de yolov8x)
- Reducir número de cámaras simultáneas

---

## Extensiones Futuras

- [ ] Soporte para múltiples lenguajes (Java, C++)
- [ ] Entrenamiento distribuido (múltiples nodos)
- [ ] Balanceo de carga automático
- [ ] Dashboard web (sin frameworks prohibidos)
- [ ] Notificaciones en tiempo real (email, SMS)
- [ ] Análisis de patrones de detección
- [ ] Exportar reportes PDF
- [ ] Soporte para más tipos de cámaras (USB, IP sin RTSP)

---

## Tecnologías Utilizadas

- **Lenguaje:** Python 3.8+
- **Modelo IA:** YOLOv8 (Ultralytics)
- **Visión Computacional:** OpenCV
- **Deep Learning:** PyTorch
- **GUI:** Tkinter
- **Comunicación:** Sockets TCP puros (sin frameworks)
- **Concurrencia:** threading (hilos)
- **Formato de Datos:** JSON
- **Protocolo de Video:** RTSP

---

## Restricciones Cumplidas

✅ **Sockets puros** - No uso de WebSocket, Socket.IO, frameworks
✅ **RTSP** - Protocolo estándar para cámaras IP
✅ **Hilos** - Concurrencia con threading
✅ **Distribuido** - Arquitectura multi-nodo
✅ **Persistencia** - Modelos y detecciones guardadas
✅ **N clases** - Configurable (COCO: 80 clases)
✅ **C cámaras** - Configurable (limitado por hardware)
✅ **Cluster** - Ejecutable en LAN/WiFi

---

## Autores

**Curso:** CC4P1 Programación Concurrente y Distribuida
**Práctica:** 04 - 2025-II
**Fecha:** Noviembre 2025

---

## Licencia

Este proyecto es parte de una práctica académica.

---

## Referencias

- [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [COCO Dataset](https://cocodataset.org/)
- [RTSP Protocol](https://en.wikipedia.org/wiki/Real_Time_Streaming_Protocol)
- [Python Socket Programming](https://docs.python.org/3/library/socket.html)

---

## Soporte

Para problemas o preguntas:
1. Revisar este README
2. Consultar `docs/INTERPRETACION_PROYECTO.md`
3. Verificar logs de los servidores
4. Probar componentes individualmente

**¡Éxito con el proyecto!** 🚀
