# Diagramas del Sistema

Este documento contiene los diagramas de arquitectura y protocolo para el informe.

---

## 1. Arquitectura del Sistema

```
┌───────────────────────────────────────────────────────────────────────┐
│                      SISTEMA DISTRIBUIDO                              │
│              Reconocimiento de Objetos en Tiempo Real                 │
└───────────────────────────────────────────────────────────────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Cámara 1  │  │   Cámara 2  │  │   Cámara C  │
│  (RTSP)     │  │  (RTSP)     │  │  (RTSP)     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │ Streams RTSP
                        ▼
        ┌───────────────────────────────┐
        │   SERVIDOR DE VIDEO           │
        │   Puerto: 5000                │
        │   • Captura multi-cámara      │
        │   • Hilos por cámara          │
        │   • Compresión frames         │
        └───────────────┬───────────────┘
                        │ Frames (TCP)
                        │ Base64 + JSON
                        ▼
        ┌───────────────────────────────┐
        │   SERVIDOR DE TESTEO          │
        │   Puerto: 5002                │
        │   • Detección YOLO            │
        │   • Pool de hilos             │
        │   • Guardado detecciones      │
        │   • Log thread-safe           │
        └───────────┬───────────────────┘
                    │
           ┌────────┴────────┐
           │                 │
           ▼                 ▼
    [Detecciones]      [Notificaciones]
    guardadas en           (TCP)
    disco + JSON           │
                           ▼
                ┌──────────────────────┐
                │  CLIENTE VIGILANTE   │
                │  • GUI Tkinter       │
                │  • Tabla detecciones │
                │  • Visor imágenes    │
                │  • Actualización RT  │
                └──────────────────────┘


    ┌─────────────────────────────────────┐
    │  SERVIDOR DE ENTRENAMIENTO          │
    │  Puerto: 5001                       │
    │  • Entrenamiento YOLO               │
    │  • Persistencia modelos             │
    │  • Métricas                         │
    └─────────────────────────────────────┘
            ▲                    │
            │ Solicitudes        │ Modelo entrenado
            │ entrenamiento      ▼
         [Cliente]          [models/mejor_modelo.pt]
```

---

## 2. Diagrama de Flujo de Datos

```
[Cámara] ──(frames)──> [Servidor Video] ──(frames TCP)──> [Servidor Testeo]
                                                                   │
                                                                   │ Detección YOLO
                                                                   ▼
                                                            ┌──────────────┐
                                                            │  Objeto?     │
                                                            └──────┬───────┘
                                                                   │ SÍ
                                    ┌──────────────────────────────┼────────────────────┐
                                    │                              │                    │
                                    ▼                              ▼                    ▼
                            [Guardar Imagen]              [Agregar a Log]      [Notificar Cliente]
                            detecciones/                   logs/detecciones          │
                            camara_X/                      .json                     │
                            timestamp.jpg                                            ▼
                                                                            [Cliente Vigilante]
                                                                            Muestra en tabla + imagen
```

---

## 3. Diagrama de Protocolo de Comunicación

### Estructura de Mensaje

```
┌──────────────────────────────────────────────────────────┐
│                    MENSAJE TCP                           │
├──────────────────────────────────────────────────────────┤
│  Header: 4 bytes                                         │
│  ┌────────────────────────────────────┐                 │
│  │  Tamaño del mensaje (Big-endian)   │                 │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Body: N bytes (JSON UTF-8)                             │
│  ┌────────────────────────────────────┐                 │
│  │ {                                  │                 │
│  │   "tipo": "FRAME",                 │                 │
│  │   "timestamp": "2025-11-25...",    │                 │
│  │   "datos": {                       │                 │
│  │     "camera_id": 1,                │                 │
│  │     "frame_data": "base64...",     │                 │
│  │     ...                            │                 │
│  │   }                                │                 │
│  │ }                                  │                 │
│  └────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────┘
```

### Secuencia de Comunicación

```
Servidor Video          Servidor Testeo        Cliente Vigilante
     │                        │                        │
     │───── FRAME ───────────>│                        │
     │   (camera_id=1)        │                        │
     │                        │                        │
     │                        │ [Procesa frame]        │
     │                        │ [Detecta objeto]       │
     │                        │                        │
     │                        │──── DETECTION ────────>│
     │                        │   (objeto="perro")     │
     │                        │                        │
     │                        │<──── ACK ──────────────│
     │                        │                        │
     │───── FRAME ───────────>│                        │
     │   (camera_id=2)        │                        │
     │                        │                        │
     │                        │ [No detecta nada]      │
     │                        │                        │
     │───── FRAME ───────────>│                        │
     │   (camera_id=1)        │                        │
     │                        │ [Detecta objeto]       │
     │                        │                        │
     │                        │──── DETECTION ────────>│
     │                        │   (objeto="gato")      │
     │                        │                        │

─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

Cliente                Servidor Entrenamiento
  │                            │
  │──── TRAIN_REQUEST ────────>│
  │  (dataset_path, epochs)    │
  │                            │
  │<────── ACK ────────────────│
  │                            │
  │                            │ [Entrenando...]
  │                            │ [Epoch 1/50]
  │                            │ [Epoch 2/50]
  │                            │ ...
  │                            │
  │<── TRAIN_COMPLETE ─────────│
  │  (modelo_path, métricas)   │
  │                            │
  │──────── ACK ───────────────>│
```

---

## 4. Diagrama de Hilos (Concurrencia)

### Servidor de Video

```
Main Thread
    │
    ├─── Socket Server Thread
    │        │
    │        ├─── Accept Clients Loop
    │        └─── Send Frames Thread
    │
    ├─── Camera 1 Capture Thread ─── [VideoCapture] ─── FrameQueue
    │
    ├─── Camera 2 Capture Thread ─── [VideoCapture] ─── FrameQueue
    │
    └─── Camera C Capture Thread ─── [VideoCapture] ─── FrameQueue
```

### Servidor de Testeo

```
Main Thread
    │
    ├─── Socket Server Thread (Vigilantes)
    │        │
    │        └─── Client Handler Threads (1 por cliente)
    │
    ├─── Frame Receiver Thread ────> Frame Queue
    │
    ├─── Processor Thread 1 ─── [YOLO Detector] ─── LogManager (Lock)
    │
    ├─── Processor Thread 2 ─── [YOLO Detector] ─── LogManager (Lock)
    │
    └─── Processor Thread N ─── [YOLO Detector] ─── LogManager (Lock)
```

### Cliente Vigilante

```
Main Thread (Tkinter Event Loop)
    │
    ├─── Receiver Thread ────> [Recibe DETECTION] ─── Lista (Lock)
    │
    └─── UI Update Loop ────> [Actualiza Tabla] <─── Lista (Lock)
```

---

## 5. Diagrama de Clases Principal

```
┌─────────────────────────────┐
│        Protocolo            │
├─────────────────────────────┤
│ + crear_mensaje()           │
│ + serializar()              │
│ + enviar_mensaje()          │
│ + recibir_mensaje()         │
│ + enviar_ack()              │
└─────────────────────────────┘
               △
               │ usa
               │
    ┌──────────┴───────────┬─────────────────┬──────────────────┐
    │                      │                 │                  │
┌───┴───────────┐  ┌──────┴────────┐  ┌────┴──────────┐  ┌───┴──────────┐
│ServidorVideo  │  │ServidorTesteo │  │ServidorEntrena│  │ClienteVigilante│
├───────────────┤  ├───────────────┤  ├───────────────┤  ├────────────────┤
│- capturas[]   │  │- detector     │  │- entrenador   │  │- socket        │
│- frame_queue  │  │- frame_queue  │  │- socket       │  │- detecciones[] │
│- socket       │  │- procesadores │  │               │  │- root (Tkinter)│
├───────────────┤  ├───────────────┤  ├───────────────┤  ├────────────────┤
│+ iniciar()    │  │+ cargar_modelo│  │+ entrenar()   │  │+ crear_interfaz│
│+ enviar()     │  │+ detectar()   │  │+ guardar()    │  │+ actualizar()  │
└───────────────┘  └───────────────┘  └───────────────┘  └────────────────┘
        │                  │                  │                   │
        │                  │                  │                   │
    ┌───▼──────┐      ┌───▼────────┐    ┌───▼────────┐          │
    │CapturaCam│      │DetectorYOLO│    │Entrenador  │          │
    │Thread    │      │            │    │YOLO        │          │
    └──────────┘      └────────────┘    └────────────┘          │
                                                                 │
    ┌─────────────────────────────────────────────────────────────┘
    │
┌───▼────────────┐
│    Utils       │
├────────────────┤
│ConfigLoader    │
│ImageUtils      │
│LogManager      │
│PathUtils       │
└────────────────┘
```

---

## 6. Diagrama de Despliegue en Cluster

```
┌────────────────────────────────────────────────────────────┐
│                         RED LAN                            │
│                      192.168.1.0/24                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────┐      ┌────────────────────┐    │
│  │   PC 1               │      │  Cámaras IP        │    │
│  │   192.168.1.10       │      │  192.168.1.100-103 │    │
│  ├──────────────────────┤      └─────────┬──────────┘    │
│  │ Servidor Video       │                │               │
│  │ Puerto: 5000         │<───── RTSP ────┘               │
│  │ • Captura C cámaras  │                                │
│  │ • Compresión frames  │                                │
│  └──────────┬───────────┘                                │
│             │ TCP 5000                                    │
│             │ (frames)                                    │
│             ▼                                             │
│  ┌──────────────────────┐                                │
│  │   PC 2               │                                │
│  │   192.168.1.20       │                                │
│  ├──────────────────────┤                                │
│  │ Servidor Testeo      │                                │
│  │ Puerto: 5002         │                                │
│  │ • Detección YOLO     │                                │
│  │ • Guardado           │                                │
│  └──────────┬───────────┘                                │
│             │ TCP 5002                                    │
│             │ (detecciones)                               │
│             ▼                                             │
│  ┌──────────────────────┐                                │
│  │   PC 3               │                                │
│  │   192.168.1.30       │                                │
│  ├──────────────────────┤                                │
│  │ Cliente Vigilante    │                                │
│  │ • GUI Tkinter        │                                │
│  │ • Monitoreo RT       │                                │
│  └──────────────────────┘                                │
│                                                            │
│  ┌──────────────────────┐                                │
│  │   PC 4 (Opcional)    │                                │
│  │   192.168.1.40       │                                │
│  ├──────────────────────┤                                │
│  │ Servidor Entrena.    │                                │
│  │ Puerto: 5001         │                                │
│  │ • GPU para entrenar  │                                │
│  └──────────────────────┘                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 7. Formato de Detección Completo

```json
{
  "id": 42,
  "camera_id": 1,
  "objeto": "perro",
  "confianza": 0.95,
  "bbox": [100, 150, 300, 400],
  "imagen_path": "detecciones/camara_1/20251125_143025.jpg",
  "timestamp": "2025-11-25T14:30:25.123456",
  "fecha": "2025-11-25",
  "hora": "14:30:25"
}
```

### Bounding Box (bbox)
```
[x1, y1, x2, y2]
 │   │   │   │
 │   │   │   └─ Coordenada Y esquina inferior derecha
 │   │   └───── Coordenada X esquina inferior derecha
 │   └───────── Coordenada Y esquina superior izquierda
 └───────────── Coordenada X esquina superior izquierda

Ejemplo visual:
    (x1, y1)
        ┌─────────────┐
        │   OBJETO    │
        │             │
        └─────────────┘
                  (x2, y2)
```

---

## 8. Ciclo de Vida de un Frame

```
1. [Cámara RTSP]
   └─> Stream continuo de video

2. [Servidor Video - CapturaCamera Thread]
   └─> cap.read() → frame (numpy array)
   └─> resize(640x480)
   └─> Frame Queue

3. [Servidor Video - Send Thread]
   └─> Obtiene frame de queue
   └─> Compresión JPEG (calidad 90)
   └─> Codificación Base64
   └─> Serialización JSON
   └─> Envío TCP con header de tamaño

4. [Servidor Testeo - Receiver Thread]
   └─> Recibe mensaje TCP
   └─> Deserialización JSON
   └─> Decodificación Base64
   └─> Frame Queue

5. [Servidor Testeo - Processor Thread]
   └─> Obtiene frame de queue
   └─> Detección YOLO
   └─> Si detecta:
       ├─> Dibujar bounding box
       ├─> Guardar imagen en disco
       ├─> Agregar a log (thread-safe)
       └─> Notificar cliente vigilante

6. [Cliente Vigilante - Receiver Thread]
   └─> Recibe detección
   └─> Agrega a lista (thread-safe)

7. [Cliente Vigilante - UI Thread]
   └─> Lee lista (thread-safe)
   └─> Actualiza tabla Tkinter
   └─> Usuario selecciona → carga y muestra imagen
```

---

## 9. Sincronización con Locks

```python
# Ejemplo: LogManager (thread-safe)

┌─────────────────────────────────────┐
│      LogManager                     │
├─────────────────────────────────────┤
│                                     │
│  Thread 1           Thread 2        │
│     │                  │            │
│     │                  │            │
│     ├─ agregar() ──┐   │            │
│     │              │   │            │
│     │         lock.acquire()        │
│     │              │   │            │
│     │              ▼   │            │
│     │         [LOCKED] │            │
│     │              │   │            │
│     │         Modifica │            │
│     │          archivo │            │
│     │              │   ├─ agregar() │
│     │              │   │  (espera)  │
│     │         lock.release()        │
│     │              │   │            │
│     │         [UNLOCKED]            │
│     │              │   │            │
│     │              │   ▼            │
│     │              │ lock.acquire() │
│     │              │   │            │
│     │              │   ▼            │
│     │              │ [LOCKED]       │
│     │              │ Modifica       │
│     │              │ archivo        │
│     │              │ lock.release() │
│                                     │
└─────────────────────────────────────┘
```

---

**Nota:** Estos diagramas están en formato texto. Para el informe final,
se recomienda recrearlos usando herramientas como:
- draw.io
- Lucidchart
- PlantUML
- Microsoft Visio
- Mermaid (para diagramas en Markdown)
