# Sistema Distribuido de Vigilancia con IA

**Práctica 04 - CC4P1 Programación Concurrente y Distribuida**

Sistema multi-lenguaje (Python + C++ + Java) para detección de objetos en tiempo real usando YOLO.

---

## 🚀 EJECUCIÓN RÁPIDA

### Necesitas 3 terminales:

**OPCIÓN A: Con limpieza automática de puertos (RECOMENDADO)**
```bash
# Terminal 1: Servidor de Testeo (Python + YOLO)
./run_servidor_testeo.sh

# Terminal 2: Servidor de Video (C++)
./run_servidor_video.sh

# Terminal 3: Cliente Vigilante (Java)
./run_java_client.sh
```

**OPCIÓN B: Ejecución directa**
```bash
# Terminal 1
python3 src/servidor_testeo/servidor_testeo.py

# Terminal 2
./src/servidor_video_cpp/servidor_video

# Terminal 3
./run_java_client.sh
```

**Si los puertos están en uso:**
```bash
./limpiar_puertos.sh    # Libera puertos 5000 y 5002
```

---

## ✅ COMPONENTES IMPLEMENTADOS

| Componente | Lenguaje | Archivo | Puerto |
|------------|----------|---------|--------|
| **Servidor Video** | C++ | `src/servidor_video_cpp/servidor_video` | 5000 |
| **Servidor Testeo** | Python | `src/servidor_testeo/servidor_testeo.py` | 5002 |
| **Cliente Vigilante** | Java | `run_java_client.sh` | - |

### Alternativas:
- Servidor Video Python: `python3 src/servidor_video/servidor_video.py`
- Cliente Python: `python3 src/cliente_vigilante/cliente_vigilante.py`

---

## 🏗️ ARQUITECTURA

```
┌─────────────┐
│ Cámara RTSP │  1920x1080
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Servidor de Video   │  C++ (alto rendimiento)
│ Puerto: 5000        │  Captura frames
└──────┬──────────────┘
       │ Sockets TCP
       ▼
┌─────────────────────┐
│ Servidor de Testeo  │  Python + YOLOv8n
│ Puerto: 5002        │  Detecta 80 objetos
└──────┬──────────────┘
       │ Detecciones
       ▼
┌─────────────────────┐
│ Cliente Vigilante   │  Java Swing GUI
│ Interfaz Gráfica    │  Muestra detecciones
└─────────────────────┘
```

---

## 📦 REQUISITOS

### Python 3.10+
```bash
pip install -r requirements.txt
```

### C++
```bash
sudo apt install libopencv-dev nlohmann-json3-dev build-essential
```

### Java
```bash
# Ya compilado, solo necesitas Java Runtime
java -version  # Debe ser 11+
```

---

## ⚙️ CONFIGURACIÓN

Edita `config/config.json`:

```json
{
  "camaras": {
    "lista": [
      {
        "id": 1,
        "rtsp_url": "rtsp://192.168.18.10:8080/h264.sdp",  // Tu cámara RTSP
        // "rtsp_url": "0",                                  // Webcam
        // "rtsp_url": "/ruta/video.mp4",                    // Video archivo
        "enabled": true
      }
    ]
  }
}
```

---

## 🎯 OBJETOS DETECTADOS (80 clases COCO)

- **Personas**: person
- **Vehículos**: car, bicycle, motorcycle, bus, truck
- **Animales**: dog, cat, bird, horse, cow
- **Tecnología**: laptop, cell phone, keyboard, mouse, tv
- **Hogar**: chair, couch, bed, bottle, cup
- Y 60+ objetos más...

---

## 📊 SALIDAS

### Interfaz Gráfica (Java/Python)
- Tabla de detecciones en tiempo real
- **Imágenes de objetos detectados** (haz clic en una fila para ver la imagen)
- Timestamps

### Archivos
```
detecciones/camara_1/
├── 20251127_HHMMSS.jpg    # Imágenes con bbox dibujados
├── 20251127_HHMMSS.jpg
└── ...

logs/detecciones.json       # Log de todas las detecciones
```

**Nota sobre guardado de imágenes**:
- Las imágenes se guardan **cada 30 frames con detección** para evitar saturación
- Esto reduce el uso de disco y mejora el rendimiento
- Si quieres cambiar la frecuencia, edita `GUARDAR_CADA_N_FRAMES` en `src/servidor_testeo/servidor_testeo.py`

---

## 🛠️ COMPILACIÓN (Ya hecho)

### C++
```bash
cd src/servidor_video_cpp
make clean && make
```

### Java
```bash
# Ya compilado en src/cliente_vigilante_java/build/
# Ejecuta con: ./run_java_client.sh
```

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Puerto en uso
```bash
pkill -f servidor_testeo
pkill -f servidor_video
pkill -f ClienteVigilante
```

### Recompilar C++
```bash
cd src/servidor_video_cpp && make clean && make
```

### Recompilar Java
```bash
mkdir -p src/cliente_vigilante_java/build
javac -d src/cliente_vigilante_java/build \
      -cp src/cliente_vigilante_java/lib/json-20231013.jar \
      src/cliente_vigilante_java/src/main/java/com/sistema/vigilante/*.java
```

### Verificar cámara
```bash
python3 test_camera.py
```

---

## 🎓 CARACTERÍSTICAS TÉCNICAS

### Concurrencia
- ✅ Python: módulo `threading`
- ✅ C++: `std::thread`
- ✅ Java: `Thread`
- ✅ Thread-safe con mutex/locks

### Comunicación
- ✅ Sockets TCP puros (sin frameworks)
- ✅ Protocolo: `[4 bytes tamaño big-endian][JSON UTF-8]`
- ✅ Compatible entre los 3 lenguajes

### IA
- ✅ YOLOv8n (Ultralytics)
- ✅ PyTorch 2.9.1
- ✅ 80 clases COCO dataset
- ✅ Transfer learning

### Redes
- ✅ RTSP para cámaras IP
- ✅ Base64 para transmisión de imágenes

---

## 📁 ESTRUCTURA

```
PC4concurrentes/
├── config/
│   └── config.json              # Configuración principal
├── src/
│   ├── servidor_video_cpp/      # C++ - Alto rendimiento
│   │   └── servidor_video       # Ejecutable compilado
│   ├── servidor_testeo/         # Python - YOLO
│   │   └── servidor_testeo.py
│   └── cliente_vigilante_java/  # Java - GUI profesional
│       ├── build/               # Clases compiladas
│       └── lib/                 # JSON library
├── logs/
│   └── detecciones.json         # Log de detecciones
├── detecciones/
│   └── camara_1/                # Imágenes guardadas
├── run_java_client.sh           # Ejecutar cliente Java
├── test_camera.py               # Probar cámaras
└── README.md                    # Este archivo
```

---

## 🏆 LENGUAJES USADOS

1. **Python** - Servidor de Testeo (IA con YOLO)
2. **C++** - Servidor de Video (máximo rendimiento)
3. **Java** - Cliente Vigilante (GUI profesional)

---

## 📝 NOTAS

- El **servidor C++** es 5-10x más rápido que Python
- El **cliente Java** tiene interfaz gráfica profesional con Swing
- Modelo **YOLOv8n** descargado automáticamente (6.3MB)
- Cámara RTSP verificada funcionando a **1920x1080**

---

**Estado**: ✅ 100% Funcional con los 3 lenguajes
**Fecha**: 2025-11-27
**Ubicación**: `/home/guido/Desktop/PC4concurrentes`
