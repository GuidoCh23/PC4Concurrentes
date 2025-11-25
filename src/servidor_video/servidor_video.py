"""
Servidor de Video - Sistema Distribuido de Reconocimiento de Objetos

Este servidor captura video desde múltiples cámaras IP (RTSP) y transmite
los frames al servidor de testeo mediante sockets puros TCP.

Características:
- Captura simultánea de C cámaras usando hilos
- Transmisión via sockets puros (sin frameworks)
- Protocolo custom definido en common/protocolo.py
"""

import cv2
import socket
import threading
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Agregar ruta del proyecto al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.common.protocolo import Protocolo, TipoMensaje, MensajeFactory
from src.common.utils import ConfigLoader, ImageUtils, ThreadSafeCounter


class CapturaCamera(threading.Thread):
    """Hilo que captura frames de una cámara específica"""

    def __init__(self, camera_config: Dict, frame_queue: 'FrameQueue',
                 resize_width: int, resize_height: int, quality: int):
        """
        Inicializa el capturador de cámara.

        Args:
            camera_config: Configuración de la cámara
            frame_queue: Cola thread-safe para almacenar frames
            resize_width: Ancho para redimensionar frames
            resize_height: Alto para redimensionar frames
            quality: Calidad de compresión JPEG (0-100)
        """
        super().__init__(daemon=True)
        self.camera_id = camera_config['id']
        self.camera_name = camera_config['nombre']
        self.rtsp_url = camera_config['rtsp_url']
        self.fps = camera_config.get('fps', 30)
        self.frame_queue = frame_queue
        self.resize_width = resize_width
        self.resize_height = resize_height
        self.quality = quality

        self.running = False
        self.capture = None
        self.frames_capturados = 0
        self.errores = 0

    def run(self):
        """Ejecuta el hilo de captura"""
        print(f"[Cámara {self.camera_id}] Iniciando captura: {self.camera_name}")

        # Validar URL RTSP
        if "(COLOCAR_AQUI" in self.rtsp_url:
            print(f"[Cámara {self.camera_id}] ERROR: URL RTSP no configurada")
            print(f"  Por favor editar config/config.json y colocar URL RTSP válida")
            print(f"  Formato: rtsp://usuario:password@IP:puerto/stream")
            return

        # Intentar conectar a la cámara
        self.capture = cv2.VideoCapture(self.rtsp_url)

        if not self.capture.isOpened():
            print(f"[Cámara {self.camera_id}] ERROR: No se pudo conectar a {self.rtsp_url}")
            return

        print(f"[Cámara {self.camera_id}] Conexión exitosa")
        self.running = True

        # Calcular delay entre frames según FPS
        frame_delay = 1.0 / self.fps

        while self.running:
            try:
                ret, frame = self.capture.read()

                if not ret:
                    print(f"[Cámara {self.camera_id}] Error leyendo frame")
                    self.errores += 1

                    # Si hay muchos errores consecutivos, intentar reconectar
                    if self.errores > 10:
                        print(f"[Cámara {self.camera_id}] Demasiados errores, intentando reconectar...")
                        self.capture.release()
                        time.sleep(2)
                        self.capture = cv2.VideoCapture(self.rtsp_url)
                        self.errores = 0

                    time.sleep(0.5)
                    continue

                # Resetear contador de errores
                self.errores = 0

                # Redimensionar frame
                frame = ImageUtils.redimensionar_frame(frame, self.resize_width, self.resize_height)

                # Agregar frame a la cola
                self.frame_queue.agregar_frame(self.camera_id, frame)
                self.frames_capturados += 1

                # Controlar FPS
                time.sleep(frame_delay)

            except Exception as e:
                print(f"[Cámara {self.camera_id}] Excepción: {e}")
                time.sleep(1)

        # Liberar recursos
        if self.capture:
            self.capture.release()
        print(f"[Cámara {self.camera_id}] Captura detenida")

    def stop(self):
        """Detiene el hilo de captura"""
        self.running = False


class FrameQueue:
    """Cola thread-safe para almacenar frames de múltiples cámaras"""

    def __init__(self, max_size: int = 100):
        """
        Inicializa la cola de frames.

        Args:
            max_size: Tamaño máximo de la cola por cámara
        """
        self.frames = {}  # {camera_id: [frames...]}
        self.lock = threading.Lock()
        self.max_size = max_size

    def agregar_frame(self, camera_id: int, frame):
        """Agrega un frame a la cola de una cámara"""
        with self.lock:
            if camera_id not in self.frames:
                self.frames[camera_id] = []

            self.frames[camera_id].append(frame)

            # Limitar tamaño de la cola
            if len(self.frames[camera_id]) > self.max_size:
                self.frames[camera_id].pop(0)

    def obtener_frame(self, camera_id: int):
        """Obtiene el frame más reciente de una cámara"""
        with self.lock:
            if camera_id in self.frames and len(self.frames[camera_id]) > 0:
                return self.frames[camera_id].pop(0)
            return None

    def tiene_frames(self, camera_id: int) -> bool:
        """Verifica si hay frames disponibles para una cámara"""
        with self.lock:
            return camera_id in self.frames and len(self.frames[camera_id]) > 0


class ServidorVideo:
    """Servidor de Video que gestiona múltiples cámaras y clientes"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Inicializa el servidor de video.

        Args:
            config_path: Ruta al archivo de configuración
        """
        # Cargar configuración
        self.config = ConfigLoader.cargar_config(config_path)
        if not self.config:
            raise Exception("No se pudo cargar la configuración")

        # Configuración del servidor
        self.host = self.config['servidor_video']['host']
        self.puerto = self.config['servidor_video']['puerto']
        self.max_clientes = self.config['servidor_video']['max_clientes']
        self.buffer_size = self.config['servidor_video']['buffer_size']

        # Configuración de frames
        self.frame_quality = self.config['servidor_video']['frame_quality']
        self.resize_width = self.config['servidor_video']['resize_width']
        self.resize_height = self.config['servidor_video']['resize_height']

        # Cámaras
        self.camaras = ConfigLoader.obtener_camaras(self.config)
        print(f"Cámaras configuradas: {len(self.camaras)}")

        # Cola de frames
        self.frame_queue = FrameQueue(max_size=self.config['concurrencia']['queue_size'])

        # Hilos de captura
        self.capturas = []

        # Socket servidor
        self.socket_servidor = None
        self.running = False

        # Clientes conectados
        self.clientes = []
        self.clientes_lock = threading.Lock()

    def iniciar_capturas(self):
        """Inicia los hilos de captura para todas las cámaras"""
        print("\n=== Iniciando captura de cámaras ===")

        for camera_config in self.camaras:
            captura = CapturaCamera(
                camera_config,
                self.frame_queue,
                self.resize_width,
                self.resize_height,
                self.frame_quality
            )
            captura.start()
            self.capturas.append(captura)

        print(f"Total de cámaras iniciadas: {len(self.capturas)}\n")

    def iniciar_servidor(self):
        """Inicia el servidor socket para aceptar clientes"""
        print(f"\n=== Servidor de Video ===")
        print(f"Iniciando servidor en {self.host}:{self.puerto}")

        # Crear socket TCP
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(self.max_clientes)

        print(f"Servidor escuchando en puerto {self.puerto}")
        print("Esperando conexiones...\n")

        self.running = True

        # Hilo para aceptar clientes
        threading.Thread(target=self._aceptar_clientes, daemon=True).start()

        # Hilo para enviar frames a clientes
        threading.Thread(target=self._enviar_frames, daemon=True).start()

    def _aceptar_clientes(self):
        """Acepta conexiones de clientes"""
        while self.running:
            try:
                cliente_socket, cliente_addr = self.socket_servidor.accept()
                print(f"[Servidor] Nueva conexión: {cliente_addr}")

                with self.clientes_lock:
                    self.clientes.append(cliente_socket)

            except Exception as e:
                if self.running:
                    print(f"[Servidor] Error aceptando cliente: {e}")

    def _enviar_frames(self):
        """Envía frames a todos los clientes conectados"""
        contador_frames = ThreadSafeCounter()

        while self.running:
            try:
                # Por cada cámara, enviar frames disponibles
                for camera_config in self.camaras:
                    camera_id = camera_config['id']

                    if self.frame_queue.tiene_frames(camera_id):
                        frame = self.frame_queue.obtener_frame(camera_id)

                        if frame is not None:
                            # Convertir frame a base64
                            frame_base64 = ImageUtils.frame_a_base64(frame, self.frame_quality)

                            # Crear mensaje
                            timestamp = datetime.now().isoformat()
                            mensaje = MensajeFactory.crear_frame(
                                camera_id,
                                frame_base64,
                                timestamp
                            )

                            # Enviar a todos los clientes
                            with self.clientes_lock:
                                clientes_desconectados = []

                                for cliente in self.clientes:
                                    try:
                                        mensaje_bytes = Protocolo.serializar(mensaje)
                                        cliente.sendall(mensaje_bytes)

                                    except Exception as e:
                                        print(f"[Servidor] Error enviando a cliente: {e}")
                                        clientes_desconectados.append(cliente)

                                # Eliminar clientes desconectados
                                for cliente in clientes_desconectados:
                                    self.clientes.remove(cliente)
                                    try:
                                        cliente.close()
                                    except:
                                        pass

                            # Estadísticas
                            contador = contador_frames.incrementar()
                            if contador % 100 == 0:
                                print(f"[Servidor] Frames enviados: {contador} | Clientes conectados: {len(self.clientes)}")

                # Pequeño delay para no saturar CPU
                time.sleep(0.01)

            except Exception as e:
                print(f"[Servidor] Error en envío de frames: {e}")
                time.sleep(0.1)

    def detener(self):
        """Detiene el servidor y todas las capturas"""
        print("\n[Servidor] Deteniendo servidor...")

        self.running = False

        # Detener capturas
        for captura in self.capturas:
            captura.stop()

        # Cerrar clientes
        with self.clientes_lock:
            for cliente in self.clientes:
                try:
                    cliente.close()
                except:
                    pass

        # Cerrar socket servidor
        if self.socket_servidor:
            self.socket_servidor.close()

        print("[Servidor] Servidor detenido")

    def ejecutar(self):
        """Ejecuta el servidor"""
        try:
            # Iniciar capturas de cámaras
            self.iniciar_capturas()

            # Iniciar servidor socket
            self.iniciar_servidor()

            # Mantener el programa corriendo
            print("Servidor ejecutándose. Presione Ctrl+C para detener.\n")

            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n[Servidor] Interrupción detectada")
        finally:
            self.detener()


def main():
    """Función principal"""
    print("=" * 60)
    print("SERVIDOR DE VIDEO - Sistema Distribuido de Reconocimiento")
    print("=" * 60)

    try:
        servidor = ServidorVideo()
        servidor.ejecutar()
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
