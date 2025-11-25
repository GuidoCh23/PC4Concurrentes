"""
Script para probar conexión a cámaras RTSP.

Este script lee la configuración de cámaras del archivo config.json
e intenta conectarse a cada una para verificar que funcionan correctamente.
"""

import cv2
import sys
import os
from pathlib import Path

# Agregar ruta del proyecto al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.common.utils import ConfigLoader


def test_camera(camera_config: dict) -> bool:
    """
    Prueba la conexión a una cámara.

    Args:
        camera_config: Configuración de la cámara

    Returns:
        True si la conexión fue exitosa
    """
    camera_id = camera_config['id']
    camera_name = camera_config['nombre']
    rtsp_url = camera_config['rtsp_url']

    print(f"\n{'='*60}")
    print(f"Probando Cámara {camera_id}: {camera_name}")
    print(f"{'='*60}")

    # Validar URL
    if "(COLOCAR_AQUI" in rtsp_url:
        print("❌ URL RTSP no configurada")
        print("   Editar config/config.json y colocar URL válida")
        print("   Formato: rtsp://usuario:password@IP:puerto/stream")
        return False

    print(f"URL: {rtsp_url}")
    print("Intentando conectar...")

    try:
        # Intentar abrir stream
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            print("❌ No se pudo conectar a la cámara")
            print("\nPosibles causas:")
            print("  - URL incorrecta")
            print("  - Credenciales inválidas")
            print("  - Cámara apagada o desconectada")
            print("  - Firewall bloqueando puerto RTSP")
            return False

        # Leer un frame de prueba
        ret, frame = cap.read()

        if not ret or frame is None:
            print("❌ Conexión establecida pero no se pudo leer frame")
            cap.release()
            return False

        # Obtener información del stream
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        print("✅ Conexión exitosa")
        print(f"\nInformación del stream:")
        print(f"  - Resolución: {width}x{height}")
        print(f"  - FPS: {fps}")
        print(f"  - Formato: {frame.dtype}")

        # Guardar frame de prueba
        test_dir = Path("test_frames")
        test_dir.mkdir(exist_ok=True)

        test_image = test_dir / f"camera_{camera_id}_test.jpg"
        cv2.imwrite(str(test_image), frame)

        print(f"  - Frame de prueba guardado: {test_image}")

        cap.release()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_webcam(camera_id: int = 0) -> bool:
    """
    Prueba la webcam local.

    Args:
        camera_id: ID de la webcam (0 para la predeterminada)

    Returns:
        True si la conexión fue exitosa
    """
    print(f"\n{'='*60}")
    print(f"Probando Webcam Local (ID: {camera_id})")
    print(f"{'='*60}")

    try:
        cap = cv2.VideoCapture(camera_id)

        if not cap.isOpened():
            print("❌ No se pudo abrir la webcam")
            return False

        ret, frame = cap.read()

        if not ret or frame is None:
            print("❌ No se pudo leer frame de la webcam")
            cap.release()
            return False

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        print("✅ Webcam funcionando correctamente")
        print(f"\nInformación:")
        print(f"  - Resolución: {width}x{height}")
        print(f"  - FPS: {fps}")

        # Guardar frame de prueba
        test_dir = Path("test_frames")
        test_dir.mkdir(exist_ok=True)

        test_image = test_dir / f"webcam_{camera_id}_test.jpg"
        cv2.imwrite(str(test_image), frame)

        print(f"  - Frame de prueba guardado: {test_image}")

        cap.release()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("SCRIPT DE PRUEBA DE CÁMARAS")
    print("=" * 60)

    # Cargar configuración
    config = ConfigLoader.cargar_config("config/config.json")

    if not config:
        print("\n❌ No se pudo cargar la configuración")
        return

    # Obtener cámaras
    camaras = ConfigLoader.obtener_camaras(config)

    print(f"\nCámaras configuradas: {len(camaras)}")

    resultados = []

    # Probar cada cámara
    for camera_config in camaras:
        exitoso = test_camera(camera_config)
        resultados.append((camera_config['nombre'], exitoso))

    # Resumen
    print(f"\n{'='*60}")
    print("RESUMEN DE PRUEBAS")
    print(f"{'='*60}")

    for nombre, exitoso in resultados:
        estado = "✅ OK" if exitoso else "❌ ERROR"
        print(f"  {nombre}: {estado}")

    exitosas = sum(1 for _, exitoso in resultados if exitoso)
    print(f"\nCámaras funcionando: {exitosas}/{len(resultados)}")

    # Opción para probar webcam local
    print(f"\n{'='*60}")
    respuesta = input("\n¿Desea probar webcam local? (s/n): ").strip().lower()

    if respuesta == 's':
        test_webcam()


if __name__ == "__main__":
    main()
