# Sistema Distribuido para Entrenamiento y Reconocimiento de Objetos con IA

## Descripción General del Proyecto

Este proyecto consiste en implementar un **sistema distribuido concurrente** que permita:
1. **Entrenar** modelos de IA para reconocimiento de objetos/animales/personas
2. **Detectar y clasificar** objetos en tiempo real desde múltiples cámaras
3. **Monitorear** los resultados mediante una interfaz de vigilancia

---

## Arquitectura del Sistema

El sistema se compone de **4 componentes principales**:

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DEL SISTEMA                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────────┐              │
│  │   Cámara 1   │────────▶│                  │              │
│  └──────────────┘         │   SERVIDOR DE    │              │
│  ┌──────────────┐         │      VIDEO       │              │
│  │   Cámara 2   │────────▶│  (Stream RTSP)   │              │
│  └──────────────┘         │                  │              │
│  ┌──────────────┐         └────────┬─────────┘              │
│  │   Cámara C   │────────▶         │                        │
│  └──────────────┘                  │ Frames                 │
│                                     ▼                        │
│                          ┌──────────────────┐               │
│                          │   SERVIDOR DE    │               │
│                          │  TESTEO/DETECCIÓN│               │
│                          │  (Usa modelo IA) │               │
│                          └────────┬─────────┘               │
│                                   │                         │
│                          Guarda: Imagen +                   │
│                          Registro (objeto,                  │
│                          fecha, hora, cámara)               │
│                                   │                         │
│  ┌────────────────────────────────┴──────────┐             │
│  │        SERVIDOR DE ENTRENAMIENTO          │             │
│  │  (Entrena modelo con inputs/outputs)      │             │
│  │  - Recibe datos de entrenamiento          │             │
│  │  - Genera y guarda modelo entrenado       │             │
│  │  - Persistencia del modelo                │             │
│  └───────────────────────────────────────────┘             │
│                      ▲                                      │
│                      │ Envía datos                         │
│                      │ entrenamiento                       │
│            ┌─────────┴──────────┐                          │
│            │  CLIENTE VIGILANTE │                          │
│            │  - Visualiza log   │                          │
│            │  - Muestra fotos   │                          │
│            │  - Info detecciones│                          │
│            └────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes Detallados

### 1. SERVIDOR DE VIDEO
**Función:** Capturar y transmitir video desde múltiples cámaras IP

**Responsabilidades:**
- Conectarse a `C` cámaras IP mediante protocolo RTSP o similar
- Capturar frames de video en tiempo real
- Distribuir frames al servidor de testeo para análisis
- Gestionar múltiples streams concurrentemente usando **hilos**

**Tecnologías sugeridas:**
- Protocolo: RTSP (Real Time Streaming Protocol)
- Comunicación: **Sockets puros** (TCP/UDP)
- (PARA CAPTURA DE VIDEO: OpenCV, FFmpeg, o similar para procesar stream RTSP)

**Parámetros importantes:**
- `C` = número de cámaras (a mayor C, mejor evaluación)

---

### 2. SERVIDOR DE ENTRENAMIENTO
**Función:** Entrenar modelos de IA para reconocimiento de objetos

**Responsabilidades:**
- Recibir datos de entrenamiento (inputs: imágenes, outputs: etiquetas)
- Entrenar el modelo de IA con `N` clases de objetos/animales/personas
- Guardar el modelo entrenado de forma persistente (archivo .h5, .pkl, .pth, etc.)
- Distribuir la carga de trabajo si es paralelo/distribuido (opcional pero valorado)

**Flujo de entrenamiento:**
```
1. Cliente/Sistema envía dataset → Servidor Entrenamiento
2. Servidor procesa datos (secuencial o distribuido)
3. Entrena modelo ML/DL (CNN, YOLO, ResNet, etc.)
4. Guarda modelo en disco
5. Notifica disponibilidad del modelo al Servidor de Testeo
```

**Requisitos de implementación:**
- El modelo puede estar en **cualquier lenguaje** (Python recomendado para IA)
- (DATASET NECESARIO: Imágenes etiquetadas de N clases - ejemplo: perros, gatos, carros, personas)
- (MODELO DE IA: Decidir arquitectura - YOLO, SSD, Faster R-CNN, MobileNet, etc.)
- Persistencia: Guardar modelo entrenado para que sea accesible
- `N` = número de clases a reconocer (mínimo 2, a mayor N mejor evaluación)

---

### 3. SERVIDOR DE TESTEO/DETECCIÓN
**Función:** Usar el modelo entrenado para detectar objetos en tiempo real

**Responsabilidades:**
- Cargar el modelo de IA entrenado
- Recibir frames del Servidor de Video
- Procesar cada frame para detectar objetos
- Cuando detecta un objeto:
  - **Guardar imagen** con bounding box
  - **Registrar en log/base de datos:**
    - Tipo de objeto detectado
    - Fecha y hora de detección
    - ID de cámara que capturó
    - Ruta de imagen guardada
- Procesar múltiples cámaras concurrentemente (hilos)

**Flujo de detección:**
```
1. Recibe frame de cámara X
2. Aplica modelo IA → Predicción
3. Si detecta objeto:
   - Dibuja bounding box
   - Guarda imagen en /detecciones/camara_X/timestamp.jpg
   - Escribe registro: {objeto, fecha, hora, cámara, imagen_path}
4. Notifica al Cliente Vigilante
```

**Formato de registro sugerido:**
```json
{
  "id": 1,
  "objeto": "Perro",
  "fecha": "2025-11-25",
  "hora": "14:30:25",
  "camara_id": 1,
  "imagen_path": "/detecciones/camara_1/20251125_143025.jpg",
  "confianza": 0.95
}
```

---

### 4. CLIENTE VIGILANTE
**Función:** Interfaz para visualizar detecciones en tiempo real

**Responsabilidades:**
- Conectarse al Servidor de Testeo
- Recibir notificaciones de detecciones en **tiempo real**
- Mostrar visualmente:
  - Tabla con registros (Objeto | Tipo | Fecha/Hora | Cámara)
  - Imagen miniatura de cada detección
  - Actualización continua (streaming de datos)

**Interfaz sugerida:**
```
┌────────────────────────────────────────────────────────┐
│          SISTEMA DE VIGILANCIA - DETECCIONES          │
├───────┬──────────┬──────────────────┬────────┬────────┤
│ Imagen│  Objeto  │   Fecha/Hora     │ Cámara │ Acción │
├───────┼──────────┼──────────────────┼────────┼────────┤
│ [IMG] │  Perro   │ 25/11/2025 14:30 │   1    │  Ver   │
│ [IMG] │  Gato    │ 25/11/2025 14:32 │   2    │  Ver   │
│ [IMG] │  Persona │ 25/11/2025 14:35 │   1    │  Ver   │
└───────┴──────────┴──────────────────┴────────┴────────┘
```

**Implementación sugerida:**
- Interfaz gráfica: (Tkinter, PyQt, Swing, JavaFX, terminal con ncurses)
- Actualización continua mediante polling o notificaciones del servidor

---

## Flujo de Trabajo Completo

### Fase 1: ENTRENAMIENTO (Offline)
```
1. Preparar dataset de N clases
   (DATASET: Recolectar/descargar imágenes de perros, gatos, carros, etc.)
2. Iniciar Servidor de Entrenamiento
3. Enviar datos de entrenamiento al servidor
4. Servidor entrena modelo
5. Modelo guardado en disco (ejemplo: modelo_objetos.h5)
```

### Fase 2: DETECCIÓN (Online/Tiempo Real)
```
1. Iniciar servidores en orden:
   a. Servidor de Entrenamiento (carga modelo existente o espera entrenamiento)
   b. Servidor de Video (conecta con cámaras)
   c. Servidor de Testeo (carga modelo entrenado)

2. Iniciar Cliente Vigilante

3. Flujo continuo:
   Cámara → [Frame] → Servidor Video → [Frame] → Servidor Testeo
                                                       ↓
                                                [Detecta objeto]
                                                       ↓
                                          [Guarda imagen + registro]
                                                       ↓
                                            Cliente Vigilante muestra
```

---

## Requisitos Técnicos OBLIGATORIOS

### Comunicación
- ✅ **Usar SOLO Sockets puros** (TCP/UDP)
- ✅ Protocolo RTSP o similar para cámaras IP
- ❌ **NO usar:** WebSocket, Socket.IO, RabbitMQ, MQ, frameworks de comunicación

### Concurrencia
- ✅ **Usar hilos** para:
  - Manejar múltiples cámaras simultáneamente
  - Evitar corrupción de registros (sincronización)
  - Mejorar desempeño del sistema

### Lenguajes de Programación
- Se puede usar **1 o más lenguajes** (LP1, LP2, LP3...)
**Implementación sugerida:**
- Interfaz gráfica: (Tkinter, PyQt, Swing, JavaFX, terminal con ncurses)
- Actualización continua mediante polling o notificaciones del servidor
- Ejemplo: Python para IA, Java para servidores, C++ para procesamiento
- (A más lenguajes, mejor puntuación)

### Despliegue
- ✅ Ejecutar en **cluster** (múltiples PCs o VMs)
- ✅ Redes LAN y WIFI
- ✅ Pruebas en tiempo real

### Persistencia
- ✅ Modelo entrenado debe guardarse y ser reutilizable
- ✅ Registros de detecciones deben almacenarse (archivo, BD simple)

---

## Parámetros de Evaluación

### N = Número de clases a reconocer
- Mínimo: 2 (ejemplo: perro, gato)
- **A mayor N, mejor puntuación**
- Sugerencias:
  - N=5: perro, gato, carro, persona, bicicleta
  - N=10: agregar: naranja, loro, manzana, laptop, celular

### C = Número de cámaras
- Mínimo: 1
- **A mayor C, mejor puntuación**
- Sugerencias: 2-4 cámaras simultáneas

### Lenguajes de programación
- Mínimo: 1
- **A más lenguajes, mejor puntuación**

---

## Elementos que Necesitan Ser Proporcionados

### (DATASET DE ENTRENAMIENTO)
**Qué:** Imágenes etiquetadas para N clases
**Dónde conseguir:**
- Kaggle Datasets
- COCO Dataset
- ImageNet
- Crear propio dataset con Google Images
**Formato:** Carpetas por clase: /dataset/perros/, /dataset/gatos/, etc.

### (MODELO DE IA - ARQUITECTURA)
**Opciones:**
- YOLO v5/v8 (recomendado para detección en tiempo real)
- SSD (Single Shot Detector)
- Faster R-CNN
- MobileNet (para dispositivos con recursos limitados)
**Framework:** TensorFlow, PyTorch, Keras, OpenCV DNN

### (CÁMARAS IP o SIMULACIÓN)
**Opciones:**
- Cámaras IP reales con RTSP
- Webcams locales
- Videos pregrabados simulando stream RTSP
- Stream simulado con OpenCV (leer video y enviar frames)

### (INTERFAZ GRÁFICA para Cliente Vigilante)
**Opciones:**
- Python: Tkinter, PyQt5, Kivy
- Java: Swing, JavaFX
- Terminal: ncurses, rich (Python)
- Web local: HTML+CSS+JS (sin frameworks prohibidos)

---

## Protocolo de Comunicación

### Formato de Mensajes (Sugerencia)
Usar un protocolo simple basado en JSON sobre sockets:

```json
// Cliente → Servidor Entrenamiento
{
  "type": "TRAIN_REQUEST",
  "dataset_path": "/path/to/dataset",
  "classes": ["perro", "gato", "carro"],
  "epochs": 50
}

// Servidor Video → Servidor Testeo
{
  "type": "FRAME",
  "camera_id": 1,
  "timestamp": "2025-11-25T14:30:25",
  "frame_data": "<base64_encoded_image>"
}

// Servidor Testeo → Cliente Vigilante
{
  "type": "DETECTION",
  "object": "Perro",
  "confidence": 0.95,
  "camera_id": 1,
  "timestamp": "2025-11-25T14:30:25",
  "image_path": "/detecciones/cam1_20251125_143025.jpg"
}
```

### Diseño del Protocolo
**(GRAFICAR: Diagrama de secuencia con mensajes entre componentes)**
```
Cliente    Srv.Entrena    Srv.Video    Srv.Testeo    Cliente Vigilante
  |              |             |            |                |
  |--TRAIN------>|             |            |                |
  |              |--TRAINING-->|            |                |
  |              |--MODEL_RDY->|----------->|                |
  |              |             |            |                |
  |              |             |--FRAME---->|                |
  |              |             |            |--DETECT------->|
  |              |             |            |                |--DISPLAY
```

---

## Diagrama de Arquitectura

**(GRAFICAR: Esquema visual de nodos y conexiones)**

```
Sugerencia de herramientas para graficar:
- draw.io
- Lucidchart
- PlantUML
- Mermaid

Elementos a incluir:
1. Nodos del sistema (servidores y cliente)
2. Flujo de datos (flechas)
3. Protocolos usados (RTSP, TCP/UDP)
4. Datos intercambiados
5. Persistencia (archivos, DB)
```

---

## Plan de Implementación Sugerido

### Fase 1: Infraestructura Básica (Semana 1)
1. Implementar servidor básico con sockets
2. Implementar cliente básico
3. Protocolo de comunicación simple
4. Pruebas de conexión en LAN

### Fase 2: Módulo de Entrenamiento (Semana 2)
1. Preparar dataset de N clases
2. Elegir y implementar modelo IA (YOLO recomendado)
3. Entrenar modelo localmente
4. Guardar modelo entrenado
5. Integrar con servidor de entrenamiento

### Fase 3: Módulo de Video (Semana 2-3)
1. Configurar captura de video (webcam o RTSP)
2. Implementar servidor de video con sockets
3. Enviar frames al servidor de testeo
4. Manejar múltiples cámaras con hilos

### Fase 4: Módulo de Testeo (Semana 3)
1. Cargar modelo entrenado
2. Procesar frames recibidos
3. Detectar objetos y guardar resultados
4. Implementar sistema de registro
5. Sincronización con hilos

### Fase 5: Cliente Vigilante (Semana 3-4)
1. Interfaz para visualizar detecciones
2. Actualización en tiempo real
3. Mostrar imágenes y registros

### Fase 6: Integración y Pruebas (Semana 4)
1. Integrar todos los componentes
2. Pruebas en cluster (múltiples PCs)
3. Pruebas en LAN y WIFI
4. Ajustes de desempeño con hilos

### Fase 7: Documentación (Semana 4)
1. Informe técnico PDF
2. Presentación PDF
3. Diagramas de arquitectura
4. Diagrama de protocolo
5. Código comentado

---

## Entregables

### 1. Código Fuente
- Archivos organizados por módulo
- Extensiones según lenguaje (LP1: .py, LP2: .java, LP3: .cpp, etc.)
- Comentarios explicativos
- README con instrucciones de ejecución

### 2. PDF Informe
**Contenido:**
- Introducción del proyecto
- Arquitectura diseñada (con diagramas)
- Protocolo de comunicación (con diagramas de secuencia)
- Explicación de módulos
- Decisiones de diseño
- Tecnologías usadas
- Pruebas realizadas
- Resultados obtenidos
- Conclusiones
- (CAPTURAS DE PANTALLA: ejecución del sistema)

### 3. PDF Presentación
**Contenido:**
- Resumen ejecutivo
- Arquitectura visual
- Demostración de funcionamiento
- Métricas (N clases, C cámaras, lenguajes)
- Conclusiones

### 4. Comprimido Final
```
proyecto_grupo.zip
├── src/
│   ├── servidor_video.py (o LP1)
│   ├── servidor_testeo.java (o LP2)
│   ├── servidor_entrenamiento.py
│   ├── cliente_vigilante.cpp (o LP3)
│   └── utils/
├── docs/
│   ├── informe.pdf
│   ├── presentacion.pdf
│   └── diagramas/
├── models/
│   └── modelo_entrenado.h5 (o formato)
├── README.md
└── requirements.txt (o dependencias)
```

---

## Restricciones y Consideraciones Importantes

### ✅ OBLIGATORIO
- Sockets puros (no frameworks)
- Hilos para concurrencia
- Protocolo RTSP o similar
- Despliegue en cluster
- Persistencia de modelos

### ❌ PROHIBIDO
- WebSocket, Socket.IO
- RabbitMQ, MQ, librerías de comunicación de alto nivel
- Frameworks de red
- (Usar solo lo mínimo necesario)

### Sincronización y Concurrencia
- **Problema:** Múltiples hilos accediendo a registros
- **Solución:** Locks, semáforos, mutex
- **Lenguajes:**
  - Python: `threading.Lock()`
  - Java: `synchronized`, `ReentrantLock`
  - C++: `std::mutex`

---

## Tecnologías Recomendadas

### Para Servidor de Video (Captura)
- Python: OpenCV, FFmpeg-python
- Java: JavaCV
- C++: OpenCV C++

### Para Modelo de IA
- Python: TensorFlow, PyTorch, Keras, YOLO
- Framework recomendado: **Ultralytics YOLOv8**

### Para Sockets
- Python: `socket`
- Java: `java.net.Socket`
- C++: `sys/socket.h`

### Para Hilos
- Python: `threading`
- Java: `java.util.concurrent`
- C++: `<thread>`

---

## Métricas de Éxito

1. ✅ Sistema funciona en cluster distribuido
2. ✅ Detecta N objetos en tiempo real (N ≥ 2)
3. ✅ Procesa C cámaras simultáneamente (C ≥ 1)
4. ✅ Registra detecciones correctamente
5. ✅ Cliente vigilante muestra info en tiempo real
6. ✅ Usa sockets puros
7. ✅ Implementado con hilos
8. ✅ Funciona en LAN y WIFI

**Puntuación extra:**
- Mayor N (más clases)
- Mayor C (más cámaras)
- Más lenguajes de programación
- Entrenamiento distribuido/paralelo

---

## Próximos Pasos

1. **Decidir N y C:** ¿Cuántas clases y cámaras?
2. **Elegir lenguajes:** ¿Python + Java? ¿Python + C++?
3. **Conseguir dataset:** Descargar o crear dataset de N clases
4. **Elegir modelo IA:** YOLO v8 recomendado
5. **Diseñar protocolo:** Definir formato de mensajes
6. **Implementar módulos:** Comenzar por servidor básico
7. **Probar en cluster:** Configurar múltiples PCs/VMs

---

## Notas Finales

- El módulo de IA puede estar en cualquier lenguaje (Python recomendado)
- Tomar como base las explicaciones del curso
- Exposición y ejecución en vivo requerida
- Código debe explicarse puntualmente
- Priorizar funcionalidad sobre complejidad innecesaria

**Fecha límite:** Subir en Univirtual según calendario del curso

---

## Contacto y Dudas

Para consultas sobre implementación:
- Revisar explicaciones del curso
- Consultar con profesor
- Coordinar con equipo para dividir tareas

---

**Documento generado:** 2025-11-25
**Curso:** CC4P1 Programación Concurrente y Distribuida
**Práctica:** 04 - 2025-II
