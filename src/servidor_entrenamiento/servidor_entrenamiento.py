"""
Servidor de Entrenamiento - Sistema Distribuido de Reconocimiento de Objetos

Este servidor entrena modelos de IA (YOLO) para reconocimiento de objetos
y responde a solicitudes de clientes mediante sockets puros TCP.

Características:
- Entrenamiento con YOLOv8 (Ultralytics)
- Comunicación via sockets puros
- Persistencia de modelos entrenados
- Soporte para datasets custom
"""

import socket
import threading
import time
import sys
import os
from typing import Dict, Optional
from pathlib import Path

# Agregar ruta del proyecto al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.common.protocolo import Protocolo, TipoMensaje
from src.common.utils import ConfigLoader

try:
    from ultralytics import YOLO
except ImportError:
    print("ERROR: ultralytics no está instalado")
    print("Instalar con: pip install ultralytics")
    YOLO = None


class EntrenadorYOLO:
    """Gestiona el entrenamiento de modelos YOLO"""

    def __init__(self, config: Dict):
        """
        Inicializa el entrenador YOLO.

        Args:
            config: Configuración del servidor de entrenamiento
        """
        self.config = config
        self.modelo_tipo = config['modelo_tipo']
        self.modelo_size = config['modelo_size']
        self.epochs = config['epochs']
        self.batch_size = config['batch_size']
        self.img_size = config['img_size']
        self.modelo_guardado = config['modelo_guardado']

        self.modelo = None
        self.entrenando = False
        self.progreso = 0

    def entrenar(self, dataset_path: str, callback=None) -> bool:
        """
        Entrena un modelo YOLO con el dataset especificado.

        Args:
            dataset_path: Ruta al archivo de configuración del dataset (data.yaml)
            callback: Función callback para reportar progreso

        Returns:
            True si el entrenamiento fue exitoso
        """
        if YOLO is None:
            print("ERROR: YOLO no está disponible")
            return False

        if self.entrenando:
            print("ERROR: Ya hay un entrenamiento en curso")
            return False

        try:
            print(f"\n=== Iniciando Entrenamiento YOLO ===")
            print(f"Dataset: {dataset_path}")
            print(f"Modelo: {self.modelo_tipo}{self.modelo_size}")
            print(f"Epochs: {self.epochs}")
            print(f"Batch size: {self.batch_size}")
            print(f"Image size: {self.img_size}")

            self.entrenando = True

            # Cargar modelo pre-entrenado base
            modelo_base = f"{self.modelo_tipo}{self.modelo_size}.pt"
            print(f"\nCargando modelo base: {modelo_base}")
            self.modelo = YOLO(modelo_base)

            # Entrenar modelo
            print("\nIniciando entrenamiento...\n")
            resultados = self.modelo.train(
                data=dataset_path,
                epochs=self.epochs,
                batch=self.batch_size,
                imgsz=self.img_size,
                patience=20,
                save=True,
                device='cpu',  # Cambiar a 'cuda' si hay GPU disponible
                workers=4,
                verbose=True
            )

            # Guardar modelo entrenado
            print(f"\nGuardando modelo entrenado en: {self.modelo_guardado}")
            os.makedirs(os.path.dirname(self.modelo_guardado), exist_ok=True)

            # Exportar el mejor modelo
            mejor_modelo = self.modelo.ckpt_path if hasattr(self.modelo, 'ckpt_path') else None
            if mejor_modelo:
                # Copiar el mejor modelo a la ubicación especificada
                import shutil
                shutil.copy(mejor_modelo, self.modelo_guardado)
            else:
                # Guardar modelo actual
                self.modelo.save(self.modelo_guardado)

            print(f"Modelo guardado exitosamente")

            # Métricas finales
            metricas = {
                "mAP50": float(resultados.results_dict.get('metrics/mAP50(B)', 0)),
                "mAP50-95": float(resultados.results_dict.get('metrics/mAP50-95(B)', 0)),
                "precision": float(resultados.results_dict.get('metrics/precision(B)', 0)),
                "recall": float(resultados.results_dict.get('metrics/recall(B)', 0))
            } if hasattr(resultados, 'results_dict') else {}

            print(f"\nMétricas finales:")
            for key, value in metricas.items():
                print(f"  {key}: {value:.4f}")

            self.entrenando = False
            return True

        except Exception as e:
            print(f"ERROR durante el entrenamiento: {e}")
            import traceback
            traceback.print_exc()
            self.entrenando = False
            return False

    def cargar_modelo(self, modelo_path: str) -> bool:
        """
        Carga un modelo YOLO previamente entrenado.

        Args:
            modelo_path: Ruta al archivo del modelo

        Returns:
            True si se cargó correctamente
        """
        if YOLO is None:
            print("ERROR: YOLO no está disponible")
            return False

        try:
            if not os.path.exists(modelo_path):
                print(f"ERROR: No existe el modelo en {modelo_path}")
                return False

            print(f"Cargando modelo desde: {modelo_path}")
            self.modelo = YOLO(modelo_path)
            print("Modelo cargado exitosamente")
            return True

        except Exception as e:
            print(f"ERROR cargando modelo: {e}")
            return False


class ServidorEntrenamiento:
    """Servidor que gestiona solicitudes de entrenamiento"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Inicializa el servidor de entrenamiento.

        Args:
            config_path: Ruta al archivo de configuración
        """
        # Cargar configuración
        self.config_general = ConfigLoader.cargar_config(config_path)
        if not self.config_general:
            raise Exception("No se pudo cargar la configuración")

        self.config = self.config_general['servidor_entrenamiento']

        # Configuración del servidor
        self.host = self.config['host']
        self.puerto = self.config['puerto']

        # Entrenador YOLO
        self.entrenador = EntrenadorYOLO(self.config)

        # Socket servidor
        self.socket_servidor = None
        self.running = False

        # Clientes conectados
        self.clientes = []
        self.clientes_lock = threading.Lock()

    def iniciar_servidor(self):
        """Inicia el servidor socket"""
        print(f"\n=== Servidor de Entrenamiento ===")
        print(f"Iniciando servidor en {self.host}:{self.puerto}")

        # Crear socket TCP
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(5)

        print(f"Servidor escuchando en puerto {self.puerto}")
        print("Esperando conexiones...\n")

        self.running = True

        # Intentar cargar modelo existente
        if os.path.exists(self.config['modelo_guardado']):
            print(f"Modelo existente encontrado: {self.config['modelo_guardado']}")
            self.entrenador.cargar_modelo(self.config['modelo_guardado'])

        # Aceptar clientes
        while self.running:
            try:
                cliente_socket, cliente_addr = self.socket_servidor.accept()
                print(f"[Servidor] Nueva conexión: {cliente_addr}")

                # Manejar cliente en un hilo separado
                cliente_thread = threading.Thread(
                    target=self._manejar_cliente,
                    args=(cliente_socket, cliente_addr),
                    daemon=True
                )
                cliente_thread.start()

            except Exception as e:
                if self.running:
                    print(f"[Servidor] Error aceptando cliente: {e}")

    def _manejar_cliente(self, cliente_socket: socket.socket, cliente_addr):
        """
        Maneja las solicitudes de un cliente.

        Args:
            cliente_socket: Socket del cliente
            cliente_addr: Dirección del cliente
        """
        print(f"[Cliente {cliente_addr}] Conexión establecida")

        try:
            while self.running:
                # Recibir mensaje
                mensaje = Protocolo.recibir_mensaje(cliente_socket)

                if not mensaje:
                    print(f"[Cliente {cliente_addr}] Desconectado")
                    break

                tipo = mensaje.get('tipo')
                datos = mensaje.get('datos', {})

                print(f"[Cliente {cliente_addr}] Mensaje recibido: {tipo}")

                # Procesar según tipo de mensaje
                if tipo == TipoMensaje.TRAIN_REQUEST:
                    self._procesar_train_request(cliente_socket, datos)

                elif tipo == TipoMensaje.LOAD_MODEL:
                    modelo_path = datos.get('modelo_path', self.config['modelo_guardado'])
                    exitoso = self.entrenador.cargar_modelo(modelo_path)

                    if exitoso:
                        Protocolo.enviar_mensaje(cliente_socket, TipoMensaje.MODEL_READY, {
                            "modelo_path": modelo_path,
                            "status": "loaded"
                        })
                    else:
                        Protocolo.enviar_error(cliente_socket, "Error cargando modelo")

                elif tipo == TipoMensaje.PING:
                    Protocolo.enviar_mensaje(cliente_socket, TipoMensaje.PONG, {})

                else:
                    print(f"[Cliente {cliente_addr}] Tipo de mensaje desconocido: {tipo}")
                    Protocolo.enviar_error(cliente_socket, f"Tipo de mensaje desconocido: {tipo}")

        except Exception as e:
            print(f"[Cliente {cliente_addr}] Error: {e}")

        finally:
            cliente_socket.close()
            print(f"[Cliente {cliente_addr}] Conexión cerrada")

    def _procesar_train_request(self, cliente_socket: socket.socket, datos: Dict):
        """
        Procesa una solicitud de entrenamiento.

        Args:
            cliente_socket: Socket del cliente
            datos: Datos de la solicitud
        """
        dataset_path = datos.get('dataset_path')
        epochs = datos.get('epochs', self.config['epochs'])

        if not dataset_path:
            Protocolo.enviar_error(cliente_socket, "dataset_path no especificado")
            return

        # Verificar que existe el dataset
        if not os.path.exists(dataset_path):
            Protocolo.enviar_error(cliente_socket, f"Dataset no encontrado: {dataset_path}")
            return

        # Actualizar epochs si se especificó
        epochs_original = self.entrenador.epochs
        if epochs:
            self.entrenador.epochs = epochs

        # Iniciar entrenamiento en un hilo separado
        def entrenar():
            print(f"\n[Entrenamiento] Iniciando con dataset: {dataset_path}")

            exitoso = self.entrenador.entrenar(dataset_path)

            if exitoso:
                print(f"[Entrenamiento] Completado exitosamente")

                # Notificar al cliente
                try:
                    Protocolo.enviar_mensaje(cliente_socket, TipoMensaje.TRAIN_COMPLETE, {
                        "status": "success",
                        "modelo_path": self.config['modelo_guardado']
                    })
                except:
                    pass
            else:
                print(f"[Entrenamiento] Falló")

                # Notificar error al cliente
                try:
                    Protocolo.enviar_error(cliente_socket, "Entrenamiento falló")
                except:
                    pass

            # Restaurar epochs original
            self.entrenador.epochs = epochs_original

        # Enviar ACK inmediato
        Protocolo.enviar_ack(cliente_socket)

        # Iniciar entrenamiento
        threading.Thread(target=entrenar, daemon=True).start()

    def detener(self):
        """Detiene el servidor"""
        print("\n[Servidor] Deteniendo servidor...")
        self.running = False

        if self.socket_servidor:
            self.socket_servidor.close()

        print("[Servidor] Servidor detenido")

    def ejecutar(self):
        """Ejecuta el servidor"""
        try:
            self.iniciar_servidor()

        except KeyboardInterrupt:
            print("\n[Servidor] Interrupción detectada")
        finally:
            self.detener()


def main():
    """Función principal"""
    print("=" * 60)
    print("SERVIDOR DE ENTRENAMIENTO - Sistema Distribuido")
    print("=" * 60)

    try:
        servidor = ServidorEntrenamiento()
        servidor.ejecutar()
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
