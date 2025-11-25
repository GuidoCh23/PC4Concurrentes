"""
Script para descargar dataset de Kaggle para entrenamiento YOLO.

Este script descarga el dataset COCO128 (versión reducida de COCO)
que contiene 128 imágenes de 80 clases diferentes.

Para usar datasets de Kaggle necesitas:
1. Cuenta en Kaggle (https://www.kaggle.com)
2. API key de Kaggle (kaggle.json)
   - Ir a: https://www.kaggle.com/settings/account
   - Scroll a "API" y click "Create New API Token"
   - Guardar kaggle.json en ~/.kaggle/ (Linux/Mac) o C:\\Users\\<username>\\.kaggle\\ (Windows)

Dataset recomendados para este proyecto:
- ultralytics/coco128: Dataset pequeño para pruebas rápidas (128 imágenes, 80 clases)
- vencerlanz09/yolov8-animal-dataset: Animales (perros, gatos, pájaros, etc.)
- andrewmvd/road-sign-detection: Señales de tráfico
"""

import os
import sys
import shutil
from pathlib import Path

# Agregar ruta del proyecto al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import kaggle
except ImportError:
    print("ERROR: kaggle no está instalado")
    print("Instalar con: pip install kaggle")
    sys.exit(1)


def descargar_coco128(destino: str = "data/coco128"):
    """
    Descarga el dataset COCO128 de Ultralytics.

    Args:
        destino: Directorio de destino
    """
    print("=" * 60)
    print("DESCARGANDO DATASET COCO128")
    print("=" * 60)

    destino_path = Path(destino)
    destino_path.mkdir(parents=True, exist_ok=True)

    try:
        print(f"\nDescargando dataset a: {destino_path.absolute()}")
        print("Esto puede tardar varios minutos...\n")

        # Descargar usando API de Kaggle
        # Nota: Ultralytics COCO128 está en GitHub, no en Kaggle
        # Usar wget o requests para descargarlo

        import urllib.request
        import zipfile

        url = "https://github.com/ultralytics/yolov5/releases/download/v1.0/coco128.zip"
        zip_path = destino_path / "coco128.zip"

        print(f"Descargando desde: {url}")

        # Descargar archivo
        urllib.request.urlretrieve(url, zip_path)

        print("Descarga completada. Extrayendo archivos...")

        # Extraer zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(destino_path.parent)

        # Eliminar zip
        zip_path.unlink()

        print("\n✓ Dataset COCO128 descargado exitosamente")
        print(f"  Ubicación: {destino_path.absolute()}")

        # Crear archivo data.yaml
        crear_data_yaml_coco128(destino_path)

        return True

    except Exception as e:
        print(f"\n✗ Error descargando dataset: {e}")
        import traceback
        traceback.print_exc()
        return False


def descargar_dataset_kaggle(dataset_slug: str, destino: str):
    """
    Descarga un dataset de Kaggle.

    Args:
        dataset_slug: Identificador del dataset (ej: 'username/dataset-name')
        destino: Directorio de destino
    """
    print("=" * 60)
    print(f"DESCARGANDO DATASET: {dataset_slug}")
    print("=" * 60)

    destino_path = Path(destino)
    destino_path.mkdir(parents=True, exist_ok=True)

    try:
        print(f"\nDescargando a: {destino_path.absolute()}")
        print("Esto puede tardar varios minutos...\n")

        # Verificar que existe kaggle.json
        kaggle_config = Path.home() / ".kaggle" / "kaggle.json"
        if not kaggle_config.exists():
            print("ERROR: No se encontró kaggle.json")
            print("\nPara configurar Kaggle API:")
            print("1. Ir a https://www.kaggle.com/settings/account")
            print("2. Scroll a 'API' y click 'Create New API Token'")
            print("3. Guardar kaggle.json en ~/.kaggle/")
            return False

        # Descargar dataset
        kaggle.api.dataset_download_files(
            dataset_slug,
            path=destino_path,
            unzip=True
        )

        print("\n✓ Dataset descargado exitosamente")
        print(f"  Ubicación: {destino_path.absolute()}")

        return True

    except Exception as e:
        print(f"\n✗ Error descargando dataset: {e}")
        import traceback
        traceback.print_exc()
        return False


def crear_data_yaml_coco128(dataset_path: Path):
    """
    Crea archivo data.yaml para COCO128 en formato YOLO.

    Args:
        dataset_path: Ruta al dataset
    """
    data_yaml_content = f"""# COCO128 Dataset para YOLO
# Clases principales de objetos comunes

path: {dataset_path.absolute()}
train: images/train2017
val: images/train2017

# Número de clases
nc: 80

# Nombres de clases
names:
  0: person
  1: bicycle
  2: car
  3: motorcycle
  4: airplane
  5: bus
  6: train
  7: truck
  8: boat
  9: traffic light
  10: fire hydrant
  11: stop sign
  12: parking meter
  13: bench
  14: bird
  15: cat
  16: dog
  17: horse
  18: sheep
  19: cow
  20: elephant
  21: bear
  22: zebra
  23: giraffe
  24: backpack
  25: umbrella
  26: handbag
  27: tie
  28: suitcase
  29: frisbee
  30: skis
  31: snowboard
  32: sports ball
  33: kite
  34: baseball bat
  35: baseball glove
  36: skateboard
  37: surfboard
  38: tennis racket
  39: bottle
  40: wine glass
  41: cup
  42: fork
  43: knife
  44: spoon
  45: bowl
  46: banana
  47: apple
  48: sandwich
  49: orange
  50: broccoli
  51: carrot
  52: hot dog
  53: pizza
  54: donut
  55: cake
  56: chair
  57: couch
  58: potted plant
  59: bed
  60: dining table
  61: toilet
  62: tv
  63: laptop
  64: mouse
  65: remote
  66: keyboard
  67: cell phone
  68: microwave
  69: oven
  70: toaster
  71: sink
  72: refrigerator
  73: book
  74: clock
  75: vase
  76: scissors
  77: teddy bear
  78: hair drier
  79: toothbrush
"""

    yaml_path = dataset_path / "data.yaml"

    with open(yaml_path, 'w') as f:
        f.write(data_yaml_content)

    print(f"\n✓ Archivo data.yaml creado: {yaml_path}")


def crear_dataset_custom(nombre: str, clases: list):
    """
    Crea estructura para dataset custom.

    Args:
        nombre: Nombre del dataset
        clases: Lista de clases
    """
    print("=" * 60)
    print(f"CREANDO ESTRUCTURA DATASET CUSTOM: {nombre}")
    print("=" * 60)

    base_path = Path("data") / nombre
    base_path.mkdir(parents=True, exist_ok=True)

    # Crear directorios
    dirs = [
        "images/train",
        "images/val",
        "labels/train",
        "labels/val"
    ]

    for dir_path in dirs:
        (base_path / dir_path).mkdir(parents=True, exist_ok=True)

    print("\n✓ Estructura de directorios creada:")
    print(f"  {base_path.absolute()}/")
    print("    ├── images/")
    print("    │   ├── train/  <- Colocar imágenes de entrenamiento aquí")
    print("    │   └── val/    <- Colocar imágenes de validación aquí")
    print("    ├── labels/")
    print("    │   ├── train/  <- Colocar etiquetas YOLO aquí")
    print("    │   └── val/    <- Colocar etiquetas YOLO aquí")
    print("    └── data.yaml")

    # Crear data.yaml
    data_yaml_content = f"""# Dataset Custom: {nombre}

path: {base_path.absolute()}
train: images/train
val: images/val

# Número de clases
nc: {len(clases)}

# Nombres de clases
names:
"""

    for i, clase in enumerate(clases):
        data_yaml_content += f"  {i}: {clase}\n"

    yaml_path = base_path / "data.yaml"

    with open(yaml_path, 'w') as f:
        f.write(data_yaml_content)

    print(f"\n✓ Archivo data.yaml creado: {yaml_path}")

    print("\nPRÓXIMOS PASOS:")
    print("1. Agregar imágenes a images/train/ y images/val/")
    print("2. Crear etiquetas en formato YOLO para cada imagen")
    print("   Formato: <clase_id> <x_center> <y_center> <width> <height>")
    print("   (valores normalizados entre 0 y 1)")
    print("3. Guardar etiquetas en labels/train/ y labels/val/")
    print(f"4. Usar {yaml_path} para entrenar el modelo")


def main():
    """Función principal"""
    print("=" * 60)
    print("SCRIPT DE DESCARGA DE DATASETS")
    print("=" * 60)

    print("\nOpciones:")
    print("1. Descargar COCO128 (recomendado para pruebas)")
    print("2. Descargar dataset de Kaggle")
    print("3. Crear estructura para dataset custom")
    print("4. Salir")

    while True:
        try:
            opcion = input("\nSeleccione una opción (1-4): ").strip()

            if opcion == '1':
                descargar_coco128()
                break

            elif opcion == '2':
                print("\nEjemplos de datasets:")
                print("  - ultralytics/coco128")
                print("  - vencerlanz09/yolov8-animal-dataset")
                print("  - andrewmvd/road-sign-detection")

                dataset_slug = input("\nIngrese dataset (formato: username/dataset-name): ").strip()
                destino = input("Directorio de destino (default: data/kaggle): ").strip()

                if not destino:
                    destino = "data/kaggle"

                descargar_dataset_kaggle(dataset_slug, destino)
                break

            elif opcion == '3':
                nombre = input("\nNombre del dataset: ").strip()
                clases_str = input("Clases separadas por coma (ej: perro,gato,pajaro): ").strip()
                clases = [c.strip() for c in clases_str.split(',')]

                crear_dataset_custom(nombre, clases)
                break

            elif opcion == '4':
                print("Saliendo...")
                break

            else:
                print("Opción inválida")

        except KeyboardInterrupt:
            print("\n\nInterrumpido por usuario")
            break


if __name__ == "__main__":
    main()
