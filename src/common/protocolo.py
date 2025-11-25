"""
Protocolo de comunicación para el sistema distribuido.
Define los tipos de mensajes y formato de comunicación entre servidores y clientes.

IMPORTANTE: Usa sockets puros (TCP) sin frameworks de comunicación.
"""

import json
import socket
import struct
from typing import Dict, Any, Optional
from datetime import datetime


class TipoMensaje:
    """Tipos de mensajes del protocolo"""
    # Servidor de Video
    FRAME = "FRAME"
    VIDEO_STATUS = "VIDEO_STATUS"

    # Servidor de Entrenamiento
    TRAIN_REQUEST = "TRAIN_REQUEST"
    TRAIN_PROGRESS = "TRAIN_PROGRESS"
    TRAIN_COMPLETE = "TRAIN_COMPLETE"
    MODEL_READY = "MODEL_READY"

    # Servidor de Testeo
    DETECTION = "DETECTION"
    TESTEO_STATUS = "TESTEO_STATUS"
    LOAD_MODEL = "LOAD_MODEL"

    # Cliente Vigilante
    GET_DETECTIONS = "GET_DETECTIONS"
    SUBSCRIBE_UPDATES = "SUBSCRIBE_UPDATES"

    # Generales
    ACK = "ACK"
    ERROR = "ERROR"
    PING = "PING"
    PONG = "PONG"


class Protocolo:
    """Maneja la serialización y deserialización de mensajes"""

    HEADER_SIZE = 4  # 4 bytes para tamaño del mensaje
    ENCODING = 'utf-8'

    @staticmethod
    def crear_mensaje(tipo: str, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un mensaje con el formato del protocolo.

        Args:
            tipo: Tipo de mensaje (de TipoMensaje)
            datos: Diccionario con los datos del mensaje

        Returns:
            Diccionario con el mensaje formateado
        """
        mensaje = {
            "tipo": tipo,
            "timestamp": datetime.now().isoformat(),
            "datos": datos
        }
        return mensaje

    @staticmethod
    def serializar(mensaje: Dict[str, Any]) -> bytes:
        """
        Serializa un mensaje a bytes para enviar por socket.

        Args:
            mensaje: Diccionario con el mensaje

        Returns:
            Bytes del mensaje con header de tamaño
        """
        # Convertir mensaje a JSON y luego a bytes
        mensaje_json = json.dumps(mensaje)
        mensaje_bytes = mensaje_json.encode(Protocolo.ENCODING)

        # Crear header con el tamaño del mensaje (4 bytes, big-endian)
        tamaño = len(mensaje_bytes)
        header = struct.pack('>I', tamaño)

        # Retornar header + mensaje
        return header + mensaje_bytes

    @staticmethod
    def enviar_mensaje(sock: socket.socket, tipo: str, datos: Dict[str, Any]) -> bool:
        """
        Crea, serializa y envía un mensaje por socket.

        Args:
            sock: Socket conectado
            tipo: Tipo de mensaje
            datos: Datos del mensaje

        Returns:
            True si se envió correctamente, False si hubo error
        """
        try:
            mensaje = Protocolo.crear_mensaje(tipo, datos)
            mensaje_bytes = Protocolo.serializar(mensaje)
            sock.sendall(mensaje_bytes)
            return True
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
            return False

    @staticmethod
    def recibir_mensaje(sock: socket.socket) -> Optional[Dict[str, Any]]:
        """
        Recibe y deserializa un mensaje del socket.

        Args:
            sock: Socket conectado

        Returns:
            Diccionario con el mensaje o None si hubo error
        """
        try:
            # Leer header (4 bytes con el tamaño)
            header_bytes = Protocolo._recibir_exacto(sock, Protocolo.HEADER_SIZE)
            if not header_bytes:
                return None

            # Extraer tamaño del mensaje
            tamaño = struct.unpack('>I', header_bytes)[0]

            # Leer mensaje completo
            mensaje_bytes = Protocolo._recibir_exacto(sock, tamaño)
            if not mensaje_bytes:
                return None

            # Deserializar JSON
            mensaje_json = mensaje_bytes.decode(Protocolo.ENCODING)
            mensaje = json.loads(mensaje_json)

            return mensaje

        except Exception as e:
            print(f"Error recibiendo mensaje: {e}")
            return None

    @staticmethod
    def _recibir_exacto(sock: socket.socket, n_bytes: int) -> Optional[bytes]:
        """
        Recibe exactamente n_bytes del socket.

        Args:
            sock: Socket conectado
            n_bytes: Número de bytes a recibir

        Returns:
            Bytes recibidos o None si se cerró la conexión
        """
        datos = bytearray()
        while len(datos) < n_bytes:
            paquete = sock.recv(n_bytes - len(datos))
            if not paquete:
                return None
            datos.extend(paquete)
        return bytes(datos)

    @staticmethod
    def enviar_ack(sock: socket.socket, mensaje_id: Optional[str] = None) -> bool:
        """Envía un mensaje de ACK"""
        datos = {"status": "ok"}
        if mensaje_id:
            datos["mensaje_id"] = mensaje_id
        return Protocolo.enviar_mensaje(sock, TipoMensaje.ACK, datos)

    @staticmethod
    def enviar_error(sock: socket.socket, error: str) -> bool:
        """Envía un mensaje de error"""
        datos = {"error": error}
        return Protocolo.enviar_mensaje(sock, TipoMensaje.ERROR, datos)


class MensajeFactory:
    """Factory para crear mensajes específicos del protocolo"""

    @staticmethod
    def crear_frame(camera_id: int, frame_base64: str, timestamp: str) -> Dict[str, Any]:
        """Crea mensaje con frame de video"""
        return Protocolo.crear_mensaje(TipoMensaje.FRAME, {
            "camera_id": camera_id,
            "frame_data": frame_base64,
            "timestamp": timestamp
        })

    @staticmethod
    def crear_deteccion(camera_id: int, objeto: str, confianza: float,
                        bbox: list, imagen_path: str) -> Dict[str, Any]:
        """Crea mensaje con detección de objeto"""
        return Protocolo.crear_mensaje(TipoMensaje.DETECTION, {
            "camera_id": camera_id,
            "objeto": objeto,
            "confianza": confianza,
            "bbox": bbox,  # [x1, y1, x2, y2]
            "imagen_path": imagen_path,
            "timestamp": datetime.now().isoformat()
        })

    @staticmethod
    def crear_train_request(dataset_path: str, clases: list, epochs: int) -> Dict[str, Any]:
        """Crea mensaje de solicitud de entrenamiento"""
        return Protocolo.crear_mensaje(TipoMensaje.TRAIN_REQUEST, {
            "dataset_path": dataset_path,
            "clases": clases,
            "epochs": epochs,
            "timestamp": datetime.now().isoformat()
        })

    @staticmethod
    def crear_train_progress(epoch: int, total_epochs: int, loss: float) -> Dict[str, Any]:
        """Crea mensaje de progreso de entrenamiento"""
        return Protocolo.crear_mensaje(TipoMensaje.TRAIN_PROGRESS, {
            "epoch": epoch,
            "total_epochs": total_epochs,
            "loss": loss,
            "porcentaje": (epoch / total_epochs) * 100
        })

    @staticmethod
    def crear_model_ready(modelo_path: str, metricas: Dict) -> Dict[str, Any]:
        """Crea mensaje de modelo listo"""
        return Protocolo.crear_mensaje(TipoMensaje.MODEL_READY, {
            "modelo_path": modelo_path,
            "metricas": metricas,
            "timestamp": datetime.now().isoformat()
        })


# Ejemplo de uso
if __name__ == "__main__":
    # Crear mensaje de prueba
    mensaje = Protocolo.crear_mensaje(TipoMensaje.DETECTION, {
        "camera_id": 1,
        "objeto": "perro",
        "confianza": 0.95
    })

    print("Mensaje creado:")
    print(json.dumps(mensaje, indent=2))

    # Serializar
    mensaje_bytes = Protocolo.serializar(mensaje)
    print(f"\nTamaño serializado: {len(mensaje_bytes)} bytes")
