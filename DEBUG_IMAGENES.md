# 🐛 Debug: Imágenes en Cliente Java

## ✅ Verificaciones Realizadas

### 1. Las imágenes SÍ se guardan
```bash
ls detecciones/camara_1/ | wc -l    # Hay imágenes
du -sh detecciones/camara_1/        # 79MB de imágenes
```

### 2. Java SÍ puede leer las imágenes
```bash
./test_imagen_java.sh               # Test exitoso ✅
```

### 3. El servidor envía rutas relativas
Ejemplo: `"imagen_path": "detecciones/camara_1/20251127_040808_222999.jpg"`

## 🔧 Mejoras Implementadas

### 1. Código Java mejorado (InterfazGUI.java)
- Intenta 4 rutas diferentes para encontrar la imagen:
  1. Ruta directa
  2. Desde directorio de trabajo (`user.dir`)
  3. Desde directorio padre
  4. Ruta absoluta hardcoded (`/home/guido/Desktop/PC4concurrentes`)

### 2. Debug habilitado
- `Deteccion.java`: Imprime ruta recibida
- `InterfazGUI.java`: Imprime ruta absoluta intentada
- `run_java_client.sh`: Muestra directorio de ejecución

## 🚀 Cómo Verificar el Problema

### Paso 1: Ejecuta el sistema
```bash
# Terminal 1
./run_servidor_testeo.sh

# Terminal 2
./run_servidor_video.sh

# Terminal 3
./run_java_client.sh     # MIRA LA CONSOLA
```

### Paso 2: Mira los logs en la consola
Deberías ver algo como:
```
[Deteccion] Ruta imagen recibida: 'detecciones/camara_1/20251127_HHMMSS.jpg'
[GUI] Cargando imagen: /home/guido/Desktop/PC4concurrentes/detecciones/camara_1/20251127_HHMMSS.jpg
```

O si falla:
```
[GUI] Imagen no encontrada: /ruta/que/probó
Working dir: /directorio/actual
```

### Paso 3: Verifica en la GUI
1. Espera a que aparezcan detecciones en la tabla
2. **HAZ CLIC en una fila de la tabla**
3. La imagen debería aparecer en el panel derecho

## 🔍 Si NO Aparece la Imagen

### Revisa la consola del cliente Java:
- ¿Qué ruta está recibiendo? (`[Deteccion] Ruta imagen recibida:`)
- ¿Qué ruta está intentando? (`[GUI] Cargando imagen:`)
- ¿Hay algún error de "Imagen no encontrada"?

### Verifica manualmente:
```bash
# ¿Existe la imagen que intentó cargar?
ls -lh /ruta/completa/que/apareció/en/el/log

# ¿El cliente está en el directorio correcto?
# Debería mostrar: /home/guido/Desktop/PC4concurrentes
```

## 📝 Notas Importantes

1. **DEBES hacer clic** en una fila de la tabla para que se muestre la imagen
2. El panel derecho está **vacío por defecto** hasta que seleccionas una detección
3. Las imágenes tienen los bounding boxes (cuadros verdes) dibujados
4. Si ves "Imagen no encontrada" con la ruta, copia esa ruta y verifica con `ls`

## ✅ Checklist

- [ ] Los 3 servidores están corriendo
- [ ] Aparecen detecciones en la tabla del cliente Java
- [ ] Hice clic en una fila de la tabla
- [ ] Revisé la consola en busca de logs de debug
- [ ] Verifiqué que las imágenes existen en `detecciones/camara_1/`

## 🆘 Si Sigue Fallando

Ejecuta esto y envía la salida:
```bash
echo "=== Test completo ==="
echo "Imágenes existentes:"
ls -lh detecciones/camara_1/ | head -5

echo -e "\nÚltima detección en log:"
tail -20 logs/detecciones.json | grep imagen_path

echo -e "\nTest de acceso Java:"
./test_imagen_java.sh
```
