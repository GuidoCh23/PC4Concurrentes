"""
Cliente Vigilante - Sistema Distribuido de Reconocimiento de Objetos

Este cliente se conecta al servidor de testeo y muestra en tiempo real
las detecciones de objetos realizadas por las cámaras.

Características:
- Interfaz gráfica con Tkinter
- Actualización en tiempo real
- Visualización de imágenes de detecciones
- Historial de detecciones
"""

import socket
import threading
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Agregar ruta del proyecto al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.common.protocolo import Protocolo, TipoMensaje
from src.common.utils import ConfigLoader

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"ERROR: Falta dependencia: {e}")
    print("Instalar con: pip install pillow")
    tk = None


class ClienteVigilante:
    """Cliente vigilante con interfaz gráfica"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Inicializa el cliente vigilante.

        Args:
            config_path: Ruta al archivo de configuración
        """
        if tk is None:
            raise Exception("Tkinter no está disponible")

        # Cargar configuración
        self.config_general = ConfigLoader.cargar_config(config_path)
        if not self.config_general:
            raise Exception("No se pudo cargar la configuración")

        self.config = self.config_general['cliente_vigilante']
        self.config_testeo = self.config_general['servidor_testeo']

        # Configuración de conexión
        self.servidor_host = self.config['servidor_testeo_host']
        self.servidor_puerto = self.config['servidor_testeo_puerto']
        self.max_registros = self.config['max_registros_mostrar']

        # Validar configuración
        if "(COLOCAR_AQUI" in self.servidor_host:
            print("ADVERTENCIA: Host del servidor de testeo no configurado")
            print("  Usando localhost por defecto")
            self.servidor_host = "127.0.0.1"

        # Socket
        self.socket = None
        self.conectado = False
        self.running = False

        # Detecciones
        self.detecciones = []
        self.detecciones_lock = threading.Lock()

        # Interfaz gráfica
        self.root = None
        self.tabla_detecciones = None
        self.imagen_label = None
        self.status_label = None
        self.stats_label = None

    def conectar_servidor(self) -> bool:
        """
        Conecta al servidor de testeo.

        Returns:
            True si se conectó exitosamente
        """
        try:
            print(f"Conectando a {self.servidor_host}:{self.servidor_puerto}...")

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.servidor_host, self.servidor_puerto))

            print("Conexión exitosa")
            self.conectado = True

            # Solicitar historial de detecciones
            Protocolo.enviar_mensaje(self.socket, TipoMensaje.GET_DETECTIONS, {
                'limite': self.max_registros
            })

            # Suscribirse a actualizaciones
            Protocolo.enviar_mensaje(self.socket, TipoMensaje.SUBSCRIBE_UPDATES, {})

            return True

        except Exception as e:
            print(f"ERROR conectando al servidor: {e}")
            return False

    def recibir_actualizaciones(self):
        """Recibe actualizaciones del servidor en tiempo real"""
        print("[Receptor] Iniciando recepción de actualizaciones...")

        while self.running and self.conectado:
            try:
                mensaje = Protocolo.recibir_mensaje(self.socket)

                if not mensaje:
                    print("[Receptor] Servidor desconectado")
                    self.conectado = False
                    break

                tipo = mensaje.get('tipo')
                datos = mensaje.get('datos', {})

                if tipo == TipoMensaje.DETECTION:
                    # Nueva detección
                    self._agregar_deteccion(datos)

                elif tipo == TipoMensaje.ACK:
                    # Respuesta a GET_DETECTIONS
                    if 'detecciones' in datos:
                        detecciones = datos['detecciones']
                        print(f"[Receptor] Recibidas {len(detecciones)} detecciones históricas")

                        for deteccion in detecciones:
                            self._agregar_deteccion(deteccion)

            except Exception as e:
                if self.running:
                    print(f"[Receptor] Error: {e}")
                    time.sleep(1)

        print("[Receptor] Detenido")

    def _agregar_deteccion(self, deteccion: Dict):
        """Agrega una detección a la lista"""
        with self.detecciones_lock:
            self.detecciones.append(deteccion)

            # Limitar tamaño del historial
            if len(self.detecciones) > self.max_registros:
                self.detecciones.pop(0)

    def crear_interfaz(self):
        """Crea la interfaz gráfica con Tkinter"""
        self.root = tk.Tk()
        self.root.title("Cliente Vigilante - Sistema de Detección de Objetos")
        self.root.geometry("1200x700")
        self.root.configure(bg='#2b2b2b')

        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header_frame = tk.Frame(main_frame, bg='#1e1e1e', relief=tk.RAISED, borderwidth=2)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = tk.Label(
            header_frame,
            text="🎥 SISTEMA DE VIGILANCIA - DETECCIONES EN TIEMPO REAL",
            font=("Arial", 16, "bold"),
            bg='#1e1e1e',
            fg='#00ff00'
        )
        title_label.pack(pady=10)

        # Status bar
        status_frame = tk.Frame(header_frame, bg='#1e1e1e')
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_label = tk.Label(
            status_frame,
            text="● Conectado" if self.conectado else "○ Desconectado",
            font=("Arial", 10),
            bg='#1e1e1e',
            fg='#00ff00' if self.conectado else '#ff0000'
        )
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.stats_label = tk.Label(
            status_frame,
            text="Detecciones: 0",
            font=("Arial", 10),
            bg='#1e1e1e',
            fg='#ffffff'
        )
        self.stats_label.pack(side=tk.LEFT, padx=20)

        # Content frame
        content_frame = tk.Frame(main_frame, bg='#2b2b2b')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Tabla de detecciones
        left_panel = tk.Frame(content_frame, bg='#2b2b2b')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        tabla_label = tk.Label(
            left_panel,
            text="HISTORIAL DE DETECCIONES",
            font=("Arial", 12, "bold"),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        tabla_label.pack(pady=(0, 5))

        # Crear tabla con Treeview
        tabla_frame = tk.Frame(left_panel, bg='#1e1e1e')
        tabla_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tabla_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(tabla_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Definir columnas
        columnas = ('id', 'objeto', 'camara', 'confianza', 'fecha', 'hora')

        self.tabla_detecciones = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show='headings',
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        # Configurar columnas
        self.tabla_detecciones.heading('id', text='ID')
        self.tabla_detecciones.heading('objeto', text='Objeto Detectado')
        self.tabla_detecciones.heading('camara', text='Cámara')
        self.tabla_detecciones.heading('confianza', text='Confianza')
        self.tabla_detecciones.heading('fecha', text='Fecha')
        self.tabla_detecciones.heading('hora', text='Hora')

        self.tabla_detecciones.column('id', width=50, anchor=tk.CENTER)
        self.tabla_detecciones.column('objeto', width=150, anchor=tk.W)
        self.tabla_detecciones.column('camara', width=80, anchor=tk.CENTER)
        self.tabla_detecciones.column('confianza', width=100, anchor=tk.CENTER)
        self.tabla_detecciones.column('fecha', width=100, anchor=tk.CENTER)
        self.tabla_detecciones.column('hora', width=100, anchor=tk.CENTER)

        self.tabla_detecciones.pack(fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.tabla_detecciones.yview)
        scrollbar_x.config(command=self.tabla_detecciones.xview)

        # Evento de selección
        self.tabla_detecciones.bind('<<TreeviewSelect>>', self._on_seleccionar_deteccion)

        # Right panel - Imagen de detección
        right_panel = tk.Frame(content_frame, bg='#1e1e1e', relief=tk.RAISED, borderwidth=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        imagen_title = tk.Label(
            right_panel,
            text="IMAGEN DE DETECCIÓN",
            font=("Arial", 12, "bold"),
            bg='#1e1e1e',
            fg='#ffffff'
        )
        imagen_title.pack(pady=10)

        # Label para mostrar imagen
        self.imagen_label = tk.Label(
            right_panel,
            text="Seleccione una detección\npara ver la imagen",
            font=("Arial", 10),
            bg='#1e1e1e',
            fg='#888888',
            width=40,
            height=20
        )
        self.imagen_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Footer con botones
        footer_frame = tk.Frame(main_frame, bg='#1e1e1e', relief=tk.RAISED, borderwidth=2)
        footer_frame.pack(fill=tk.X, pady=(10, 0))

        btn_actualizar = tk.Button(
            footer_frame,
            text="Actualizar",
            command=self._actualizar_manual,
            font=("Arial", 10),
            bg='#3a3a3a',
            fg='#ffffff',
            activebackground='#4a4a4a',
            padx=20,
            pady=5
        )
        btn_actualizar.pack(side=tk.LEFT, padx=10, pady=10)

        btn_limpiar = tk.Button(
            footer_frame,
            text="Limpiar",
            command=self._limpiar_tabla,
            font=("Arial", 10),
            bg='#3a3a3a',
            fg='#ffffff',
            activebackground='#4a4a4a',
            padx=20,
            pady=5
        )
        btn_limpiar.pack(side=tk.LEFT, padx=10, pady=10)

    def _actualizar_manual(self):
        """Solicita actualización manual de detecciones"""
        if self.conectado:
            try:
                Protocolo.enviar_mensaje(self.socket, TipoMensaje.GET_DETECTIONS, {
                    'limite': self.max_registros
                })
            except:
                pass

    def _limpiar_tabla(self):
        """Limpia la tabla de detecciones"""
        with self.detecciones_lock:
            self.detecciones.clear()

        # Limpiar treeview
        for item in self.tabla_detecciones.get_children():
            self.tabla_detecciones.delete(item)

        # Limpiar imagen
        self.imagen_label.config(
            image='',
            text="Seleccione una detección\npara ver la imagen"
        )

    def _on_seleccionar_deteccion(self, event):
        """Maneja la selección de una detección en la tabla"""
        seleccion = self.tabla_detecciones.selection()

        if not seleccion:
            return

        item = seleccion[0]
        valores = self.tabla_detecciones.item(item, 'values')

        if not valores:
            return

        # Obtener ID de la detección
        deteccion_id = int(valores[0])

        # Buscar detección completa
        with self.detecciones_lock:
            deteccion = next(
                (d for d in self.detecciones if d.get('id') == deteccion_id),
                None
            )

        if deteccion and 'imagen_path' in deteccion:
            self._mostrar_imagen(deteccion['imagen_path'])

    def _mostrar_imagen(self, imagen_path: str):
        """Muestra una imagen de detección"""
        try:
            if not os.path.exists(imagen_path):
                self.imagen_label.config(
                    image='',
                    text=f"Imagen no encontrada:\n{imagen_path}"
                )
                return

            # Cargar y redimensionar imagen
            imagen = Image.open(imagen_path)

            # Redimensionar manteniendo aspecto
            max_width = 400
            max_height = 400

            ratio = min(max_width / imagen.width, max_height / imagen.height)
            nuevo_width = int(imagen.width * ratio)
            nuevo_height = int(imagen.height * ratio)

            imagen = imagen.resize((nuevo_width, nuevo_height), Image.Resampling.LANCZOS)

            # Convertir a PhotoImage
            photo = ImageTk.PhotoImage(imagen)

            # Mostrar en label (guardar referencia para evitar garbage collection)
            self.imagen_label.config(image=photo, text='')
            self.imagen_label.image = photo

        except Exception as e:
            self.imagen_label.config(
                image='',
                text=f"Error cargando imagen:\n{str(e)}"
            )

    def actualizar_interfaz(self):
        """Actualiza la interfaz con nuevas detecciones"""
        try:
            with self.detecciones_lock:
                # Obtener IDs actuales en la tabla
                items_actuales = set()
                for item in self.tabla_detecciones.get_children():
                    valores = self.tabla_detecciones.item(item, 'values')
                    if valores:
                        items_actuales.add(int(valores[0]))

                # Agregar nuevas detecciones
                for deteccion in self.detecciones:
                    det_id = deteccion.get('id', 0)

                    if det_id not in items_actuales:
                        valores = (
                            det_id,
                            deteccion.get('objeto', 'N/A'),
                            f"Cámara {deteccion.get('camera_id', 'N/A')}",
                            f"{deteccion.get('confianza', 0):.2f}",
                            deteccion.get('fecha', 'N/A'),
                            deteccion.get('hora', 'N/A')
                        )

                        self.tabla_detecciones.insert('', 0, values=valores)

                # Actualizar estadísticas
                total_detecciones = len(self.detecciones)
                self.stats_label.config(text=f"Detecciones: {total_detecciones}")

                # Actualizar status
                if self.conectado:
                    self.status_label.config(text="● Conectado", fg='#00ff00')
                else:
                    self.status_label.config(text="○ Desconectado", fg='#ff0000')

            # Programar siguiente actualización
            if self.running:
                self.root.after(1000, self.actualizar_interfaz)

        except Exception as e:
            print(f"Error actualizando interfaz: {e}")

    def ejecutar(self):
        """Ejecuta el cliente vigilante"""
        try:
            print("=" * 60)
            print("CLIENTE VIGILANTE")
            print("=" * 60)

            # Conectar al servidor
            if not self.conectar_servidor():
                print("\nERROR: No se pudo conectar al servidor")
                print("  Asegúrate de que el servidor de testeo esté ejecutándose")
                return

            self.running = True

            # Iniciar hilo de recepción
            receptor_thread = threading.Thread(target=self.recibir_actualizaciones, daemon=True)
            receptor_thread.start()

            # Crear interfaz
            self.crear_interfaz()

            # Iniciar actualización de interfaz
            self.root.after(1000, self.actualizar_interfaz)

            # Ejecutar loop de Tkinter
            self.root.mainloop()

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.detener()

    def detener(self):
        """Detiene el cliente"""
        print("\n[Cliente] Deteniendo cliente...")
        self.running = False
        self.conectado = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        print("[Cliente] Cliente detenido")


def main():
    """Función principal"""
    try:
        cliente = ClienteVigilante()
        cliente.ejecutar()
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
