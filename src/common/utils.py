"""
Utilidades comunes para el sistema distribuido.
"""

import json
import os
import base64
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading


class ConfigLoader:
    """Carga y gestiona la configuración del sistema"""

    @staticmethod
    def cargar_config(ruta: str = "config/config.json") -> Dict[str, Any]:
        """
        Carga el archivo de configuración JSON.

        Args:
            ruta: Ruta al archivo de configuración

        Returns:
            Diccionario con la configuración
        """
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo de configuración en {ruta}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error al parsear JSON: {e}")
            return {}

    @staticmethod
    def obtener_camaras(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtiene la lista de cámaras habilitadas"""
        camaras = config.get('camaras', {}).get('lista', [])
        return [cam for cam in camaras if cam.get('enabled', True)]

    @staticmethod
    def validar_rtsp_url(url: str) -> bool:
        """Valida que la URL RTSP esté completa"""
        if "(COLOCAR_AQUI" in url:
            return False
        if not url.startswith("rtsp://"):
            return False
        return True


class ImageUtils:
    """Utilidades para procesamiento de imágenes"""

    @staticmethod
    def frame_a_base64(frame: np.ndarray, quality: int = 90) -> str:
        """
        Convierte un frame de OpenCV a string base64.

        Args:
            frame: Frame de OpenCV (numpy array)
            quality: Calidad de compresión JPEG (0-100)

        Returns:
            String base64 del frame
        """
        # Codificar frame a JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        # Convertir a base64
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return frame_base64

    @staticmethod
    def base64_a_frame(frame_base64: str) -> Optional[np.ndarray]:
        """
        Convierte string base64 a frame de OpenCV.

        Args:
            frame_base64: String base64 del frame

        Returns:
            Frame de OpenCV (numpy array) o None si hay error
        """
        try:
            # Decodificar base64
            frame_bytes = base64.b64decode(frame_base64)
            # Convertir bytes a numpy array
            nparr = np.frombuffer(frame_bytes, np.uint8)
            # Decodificar imagen
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"Error decodificando frame: {e}")
            return None

    @staticmethod
    def redimensionar_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """Redimensiona un frame"""
        return cv2.resize(frame, (width, height))

    @staticmethod
    def dibujar_deteccion(frame: np.ndarray, bbox: List[int],
                          clase: str, confianza: float) -> np.ndarray:
        """
        Dibuja bounding box y etiqueta en un frame.

        Args:
            frame: Frame de OpenCV
            bbox: [x1, y1, x2, y2]
            clase: Nombre de la clase detectada
            confianza: Confianza de la detección (0-1)

        Returns:
            Frame con detección dibujada
        """
        x1, y1, x2, y2 = bbox

        # Dibujar rectángulo
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Preparar etiqueta
        etiqueta = f"{clase}: {confianza:.2f}"

        # Calcular tamaño del texto
        (w, h), _ = cv2.getTextSize(etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)

        # Dibujar fondo de la etiqueta
        cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), (0, 255, 0), -1)

        # Dibujar texto
        cv2.putText(frame, etiqueta, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        return frame

    @staticmethod
    def guardar_imagen(frame: np.ndarray, ruta: str) -> bool:
        """Guarda un frame en disco"""
        try:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            cv2.imwrite(ruta, frame)
            return True
        except Exception as e:
            print(f"Error guardando imagen: {e}")
            return False


class LogManager:
    """Gestiona los logs de detecciones"""

    def __init__(self, log_path: str = "logs/detecciones.json"):
        self.log_path = log_path
        self.lock = threading.Lock()
        self._inicializar_log()

    def _inicializar_log(self):
        """Crea el archivo de log si no existe"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def agregar_deteccion(self, deteccion: Dict[str, Any]):
        """
        Agrega una detección al log de forma thread-safe.

        Args:
            deteccion: Diccionario con información de la detección
        """
        with self.lock:
            try:
                # Leer log actual
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    detecciones = json.load(f)

                # Agregar nueva detección
                detecciones.append(deteccion)

                # Guardar log actualizado
                with open(self.log_path, 'w', encoding='utf-8') as f:
                    json.dump(detecciones, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"Error agregando detección al log: {e}")

    def obtener_detecciones(self, limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las detecciones del log.

        Args:
            limite: Número máximo de detecciones a retornar (None = todas)

        Returns:
            Lista de detecciones
        """
        with self.lock:
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    detecciones = json.load(f)

                if limite:
                    return detecciones[-limite:]
                return detecciones

            except Exception as e:
                print(f"Error leyendo log: {e}")
                return []

    def limpiar_log(self):
        """Limpia el log de detecciones"""
        with self.lock:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)


class PathUtils:
    """Utilidades para manejo de rutas"""

    @staticmethod
    def crear_ruta_deteccion(camera_id: int, base_path: str = "detecciones") -> str:
        """
        Crea ruta para guardar imagen de detección.

        Args:
            camera_id: ID de la cámara
            base_path: Ruta base para detecciones

        Returns:
            Ruta completa con timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        directorio = os.path.join(base_path, f"camara_{camera_id}")
        os.makedirs(directorio, exist_ok=True)
        return os.path.join(directorio, f"{timestamp}.jpg")

    @staticmethod
    def obtener_proyecto_root() -> str:
        """Obtiene la ruta raíz del proyecto"""
        # Asume que utils.py está en src/common/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(current_dir))


class ThreadSafeCounter:
    """Contador thread-safe para IDs"""

    def __init__(self, inicio: int = 0):
        self.valor = inicio
        self.lock = threading.Lock()

    def incrementar(self) -> int:
        """Incrementa y retorna el valor actual"""
        with self.lock:
            self.valor += 1
            return self.valor

    def obtener(self) -> int:
        """Obtiene el valor actual sin incrementar"""
        with self.lock:
            return self.valor


# Ejemplo de uso
if __name__ == "__main__":
    # Probar carga de configuración
    config = ConfigLoader.cargar_config("../../config/config.json")
    if config:
        print("Configuración cargada:")
        print(f"- Sistema: {config.get('sistema', {}).get('nombre')}")
        print(f"- Número de cámaras: {config.get('camaras', {}).get('cantidad')}")

        camaras = ConfigLoader.obtener_camaras(config)
        print(f"\nCámaras habilitadas: {len(camaras)}")
        for cam in camaras:
            print(f"  - {cam['nombre']} (ID: {cam['id']})")
