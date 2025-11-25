"""
Servidor de Testeo/Detección - Sistema Distribuido de Reconocimiento de Objetos

Este servidor recibe frames del servidor de video, aplica el modelo YOLO entrenado
para detectar objetos, guarda las detecciones y notifica al cliente vigilante.

Características:
- Detección en tiempo real con YOLO
- Procesamiento multi-cámara con hilos
- Guardado automático de detecciones
- Log de detecciones thread-safe
- Comunicación via sockets puros
"""

import socket
import threading
import time
import sys
import os
from datetime import datetime
from typing import Dict, Optional, List
import queue

# Agregar ruta del proyecto al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.common.protocolo import Protocolo, TipoMensaje, MensajeFactory
from src.common.utils import ConfigLoader, ImageUtils, LogManager, PathUtils

try:
    from ultralytics import YOLO
    import cv2
    import numpy as np
except ImportError as e:
    print(f"ERROR: Falta dependencia: {e}")
    print("Instalar con: pip install ultralytics opencv-python")
    YOLO = None


class DetectorYOLO:
    """Gestiona la detección de objetos con YOLO"""

    def __init__(self, config: Dict):
        """
        Inicializa el detector YOLO.

        Args:
            config: Configuración del servidor de testeo
        """
        self.config = config
        self.modelo_path = config['modelo_path']
        self.confidence_threshold = config['confidence_threshold']
        self.iou_threshold = config['iou_threshold']

        self.modelo = None
        self.modelo_cargado = False

    def cargar_modelo(self) -> bool:
        """
        Carga el modelo YOLO entrenado.

        Returns:
            True si se cargó correctamente
        """
        if YOLO is None:
            print("ERROR: YOLO no está disponible")
            return False

        try:
            if not os.path.exists(self.modelo_path):
                print(f"ADVERTENCIA: Modelo no encontrado en {self.modelo_path}")
                print("  Opciones:")
                print("  1. Entrenar un modelo usando el servidor de entrenamiento")
                print("  2. Usar un modelo pre-entrenado (yolov8n.pt)")

                # Intentar cargar modelo pre-entrenado base
                print("\nIntentando cargar modelo base yolov8n.pt...")
                self.modelo = YOLO('yolov8n.pt')
                self.modelo_cargado = True
                print("Modelo base cargado (usar solo para pruebas)")
                return True

            print(f"Cargando modelo desde: {self.modelo_path}")
            self.modelo = YOLO(self.modelo_path)
            self.modelo_cargado = True
            print("Modelo cargado exitosamente")

            # Mostrar clases del modelo
            if hasattr(self.modelo, 'names'):
                print(f"Clases del modelo: {list(self.modelo.names.values())}")

            return True

        except Exception as e:
            print(f"ERROR cargando modelo: {e}")
            import traceback
            traceback.print_exc()
            return False

    def detectar(self, frame: np.ndarray) -> List[Dict]:
        """
        Detecta objetos en un frame.

        Args:
            frame: Frame de OpenCV (numpy array)

        Returns:
            Lista de detecciones con formato:
            [{
                'clase': str,
                'confianza': float,
                'bbox': [x1, y1, x2, y2]
            }, ...]
        """
        if not self.modelo_cargado or self.modelo is None:
            return []

        try:
            # Ejecutar detección
            resultados = self.modelo.predict(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False
            )

            detecciones = []

            # Procesar resultados
            for resultado in resultados:
                boxes = resultado.boxes

                for box in boxes:
                    # Extraer información
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confianza = float(box.conf[0].cpu().numpy())
                    clase_id = int(box.cls[0].cpu().numpy())
                    clase_nombre = self.modelo.names[clase_id]

                    deteccion = {
                        'clase': clase_nombre,
                        'confianza': confianza,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)]
                    }

                    detecciones.append(deteccion)

            return detecciones

        except Exception as e:
            print(f"ERROR en detección: {e}")
            return []


class ProcesadorFrames(threading.Thread):
    """Hilo que procesa frames y detecta objetos"""

    def __init__(self, frame_queue: queue.Queue, detector: DetectorYOLO,
                 log_manager: LogManager, config: Dict,
                 notificador_callback):
        """
        Inicializa el procesador de frames.

        Args:
            frame_queue: Cola de frames a procesar
            detector: Detector YOLO
            log_manager: Gestor de logs
            config: Configuración
            notificador_callback: Callback para notificar detecciones
        """
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.detector = detector
        self.log_manager = log_manager
        self.config = config
        self.notificador_callback = notificador_callback

        self.running = False
        self.frames_procesados = 0

    def run(self):
        """Ejecuta el procesamiento de frames"""
        print("[Procesador] Iniciado")
        self.running = True

        while self.running:
            try:
                # Obtener frame de la cola (timeout de 1 segundo)
                try:
                    frame_data = self.frame_queue.get(timeout=1)
                except queue.Empty:
                    continue

                camera_id = frame_data['camera_id']
                frame = frame_data['frame']
                timestamp = frame_data['timestamp']

                # Detectar objetos
                detecciones = self.detector.detectar(frame)

                # Procesar cada detección
                for deteccion in detecciones:
                    # Dibujar detección en el frame
                    frame_con_bbox = ImageUtils.dibujar_deteccion(
                        frame.copy(),
                        deteccion['bbox'],
                        deteccion['clase'],
                        deteccion['confianza']
                    )

                    # Guardar imagen
                    imagen_path = PathUtils.crear_ruta_deteccion(
                        camera_id,
                        self.config['detecciones_path']
                    )

                    if ImageUtils.guardar_imagen(frame_con_bbox, imagen_path):
                        # Crear registro de detección
                        registro = {
                            'id': self.frames_procesados,
                            'camera_id': camera_id,
                            'objeto': deteccion['clase'],
                            'confianza': deteccion['confianza'],
                            'bbox': deteccion['bbox'],
                            'imagen_path': imagen_path,
                            'timestamp': timestamp,
                            'fecha': datetime.now().strftime("%Y-%m-%d"),
                            'hora': datetime.now().strftime("%H:%M:%S")
                        }

                        # Agregar al log
                        self.log_manager.agregar_deteccion(registro)

                        # Notificar al cliente vigilante
                        if self.notificador_callback:
                            self.notificador_callback(registro)

                        print(f"[Detección] Cámara {camera_id}: {deteccion['clase']} ({deteccion['confianza']:.2f})")

                self.frames_procesados += 1

                if self.frames_procesados % 50 == 0:
                    print(f"[Procesador] Frames procesados: {self.frames_procesados}")

            except Exception as e:
                print(f"[Procesador] Error: {e}")
                time.sleep(0.1)

        print("[Procesador] Detenido")

    def stop(self):
        """Detiene el procesador"""
        self.running = False


class ServidorTesteo:
    """Servidor de testeo/detección de objetos"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Inicializa el servidor de testeo.

        Args:
            config_path: Ruta al archivo de configuración
        """
        # Cargar configuración
        self.config_general = ConfigLoader.cargar_config(config_path)
        if not self.config_general:
            raise Exception("No se pudo cargar la configuración")

        self.config = self.config_general['servidor_testeo']
        self.config_video = self.config_general['servidor_video']

        # Configuración del servidor
        self.host = self.config['host']
        self.puerto = self.config['puerto']

        # Detector YOLO
        self.detector = DetectorYOLO(self.config)

        # Log manager
        self.log_manager = LogManager(self.config['log_path'])

        # Cola de frames para procesar
        self.frame_queue = queue.Queue(maxsize=self.config_general['concurrencia']['queue_size'])

        # Procesadores de frames (hilos)
        self.procesadores = []
        self.num_procesadores = self.config_general['concurrencia']['max_hilos_testeo']

        # Socket servidor para clientes vigilantes
        self.socket_servidor = None
        self.running = False

        # Socket cliente para conectar a servidor de video
        self.socket_video = None
        self.video_host = self.config_video['host']
        self.video_puerto = self.config_video['puerto']

        # Clientes vigilantes conectados
        self.clientes_vigilantes = []
        self.clientes_lock = threading.Lock()

    def cargar_modelo(self) -> bool:
        """Carga el modelo YOLO"""
        return self.detector.cargar_modelo()

    def conectar_servidor_video(self) -> bool:
        """
        Conecta al servidor de video para recibir frames.

        Returns:
            True si se conectó exitosamente
        """
        try:
            # Validar configuración
            if "(COLOCAR_AQUI" in self.video_host:
                print("ADVERTENCIA: Host del servidor de video no configurado")
                print("  Usando localhost por defecto")
                self.video_host = "127.0.0.1"

            print(f"\nConectando al servidor de video: {self.video_host}:{self.video_puerto}")

            self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_video.connect((self.video_host, self.video_puerto))

            print("Conexión exitosa al servidor de video")
            return True

        except Exception as e:
            print(f"ERROR conectando al servidor de video: {e}")
            print("  Asegúrate de que el servidor de video esté ejecutándose")
            return False

    def iniciar_procesadores(self):
        """Inicia los hilos procesadores de frames"""
        print(f"\nIniciando {self.num_procesadores} procesadores...")

        for i in range(self.num_procesadores):
            procesador = ProcesadorFrames(
                self.frame_queue,
                self.detector,
                self.log_manager,
                self.config,
                self._notificar_deteccion
            )
            procesador.start()
            self.procesadores.append(procesador)

        print(f"Procesadores iniciados: {len(self.procesadores)}")

    def _notificar_deteccion(self, deteccion: Dict):
        """
        Notifica una detección a todos los clientes vigilantes.

        Args:
            deteccion: Diccionario con la detección
        """
        with self.clientes_lock:
            clientes_desconectados = []

            for cliente in self.clientes_vigilantes:
                try:
                    Protocolo.enviar_mensaje(cliente, TipoMensaje.DETECTION, deteccion)
                except Exception as e:
                    print(f"[Notificador] Error enviando a cliente: {e}")
                    clientes_desconectados.append(cliente)

            # Eliminar clientes desconectados
            for cliente in clientes_desconectados:
                self.clientes_vigilantes.remove(cliente)
                try:
                    cliente.close()
                except:
                    pass

    def recibir_frames(self):
        """Recibe frames del servidor de video"""
        print("\n[Receptor] Iniciando recepción de frames...")

        while self.running:
            try:
                # Recibir mensaje
                mensaje = Protocolo.recibir_mensaje(self.socket_video)

                if not mensaje:
                    print("[Receptor] Servidor de video desconectado")
                    break

                tipo = mensaje.get('tipo')

                if tipo == TipoMensaje.FRAME:
                    datos = mensaje['datos']
                    camera_id = datos['camera_id']
                    frame_base64 = datos['frame_data']
                    timestamp = datos['timestamp']

                    # Decodificar frame
                    frame = ImageUtils.base64_a_frame(frame_base64)

                    if frame is not None:
                        # Agregar a la cola de procesamiento
                        try:
                            self.frame_queue.put({
                                'camera_id': camera_id,
                                'frame': frame,
                                'timestamp': timestamp
                            }, block=False)
                        except queue.Full:
                            # Cola llena, descartar frame
                            pass

            except Exception as e:
                if self.running:
                    print(f"[Receptor] Error: {e}")
                    time.sleep(1)

        print("[Receptor] Detenido")

    def iniciar_servidor_vigilantes(self):
        """Inicia servidor para aceptar clientes vigilantes"""
        print(f"\nIniciando servidor para clientes vigilantes en puerto {self.puerto}...")

        # Crear socket TCP
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(5)

        print(f"Servidor escuchando en puerto {self.puerto}")

        # Hilo para aceptar clientes
        threading.Thread(target=self._aceptar_vigilantes, daemon=True).start()

    def _aceptar_vigilantes(self):
        """Acepta conexiones de clientes vigilantes"""
        while self.running:
            try:
                cliente_socket, cliente_addr = self.socket_servidor.accept()
                print(f"[Vigilante] Nueva conexión: {cliente_addr}")

                with self.clientes_lock:
                    self.clientes_vigilantes.append(cliente_socket)

                # Manejar solicitudes del cliente en un hilo
                threading.Thread(
                    target=self._manejar_vigilante,
                    args=(cliente_socket, cliente_addr),
                    daemon=True
                ).start()

            except Exception as e:
                if self.running:
                    print(f"[Vigilante] Error aceptando cliente: {e}")

    def _manejar_vigilante(self, cliente_socket: socket.socket, cliente_addr):
        """Maneja solicitudes de un cliente vigilante"""
        try:
            while self.running:
                mensaje = Protocolo.recibir_mensaje(cliente_socket)

                if not mensaje:
                    break

                tipo = mensaje.get('tipo')
                datos = mensaje.get('datos', {})

                if tipo == TipoMensaje.GET_DETECTIONS:
                    # Enviar historial de detecciones
                    limite = datos.get('limite', 100)
                    detecciones = self.log_manager.obtener_detecciones(limite)

                    Protocolo.enviar_mensaje(cliente_socket, TipoMensaje.ACK, {
                        'detecciones': detecciones,
                        'total': len(detecciones)
                    })

                elif tipo == TipoMensaje.SUBSCRIBE_UPDATES:
                    # Cliente ya está suscrito automáticamente
                    Protocolo.enviar_ack(cliente_socket)

        except Exception as e:
            print(f"[Vigilante {cliente_addr}] Error: {e}")

        finally:
            with self.clientes_lock:
                if cliente_socket in self.clientes_vigilantes:
                    self.clientes_vigilantes.remove(cliente_socket)

            cliente_socket.close()
            print(f"[Vigilante {cliente_addr}] Desconectado")

    def ejecutar(self):
        """Ejecuta el servidor"""
        try:
            print("=" * 60)
            print("SERVIDOR DE TESTEO/DETECCIÓN")
            print("=" * 60)

            # Cargar modelo
            if not self.cargar_modelo():
                print("\nERROR: No se pudo cargar el modelo")
                return

            # Iniciar procesadores
            self.iniciar_procesadores()

            # Iniciar servidor para clientes vigilantes
            self.iniciar_servidor_vigilantes()

            # Conectar al servidor de video
            if not self.conectar_servidor_video():
                print("\nERROR: No se pudo conectar al servidor de video")
                return

            self.running = True

            # Iniciar recepción de frames
            self.recibir_frames()

        except KeyboardInterrupt:
            print("\n[Servidor] Interrupción detectada")
        finally:
            self.detener()

    def detener(self):
        """Detiene el servidor"""
        print("\n[Servidor] Deteniendo servidor...")
        self.running = False

        # Detener procesadores
        for procesador in self.procesadores:
            procesador.stop()

        # Cerrar sockets
        if self.socket_video:
            self.socket_video.close()

        if self.socket_servidor:
            self.socket_servidor.close()

        print("[Servidor] Servidor detenido")


def main():
    """Función principal"""
    try:
        servidor = ServidorTesteo()
        servidor.ejecutar()
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
