#!/usr/bin/env python3
"""Cliente simple para probar el servidor de testeo"""
import socket
import json
import struct

def recibir_mensaje(sock):
    # Recibir header (4 bytes)
    header = sock.recv(4)
    if len(header) < 4:
        return None

    tamano = struct.unpack('!I', header)[0]

    # Recibir body
    data = b''
    while len(data) < tamano:
        chunk = sock.recv(tamano - len(data))
        if not chunk:
            return None
        data += chunk

    return json.loads(data.decode('utf-8'))

def enviar_mensaje(sock, tipo, datos):
    mensaje = {
        'tipo': tipo,
        'datos': datos,
        'timestamp': '2025-11-27T00:00:00'
    }
    mensaje_str = json.dumps(mensaje)
    mensaje_bytes = mensaje_str.encode('utf-8')

    # Enviar header + body
    header = struct.pack('!I', len(mensaje_bytes))
    sock.sendall(header + mensaje_bytes)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 5002))

    print("✅ Conectado al servidor")

    # Solicitar historial
    enviar_mensaje(sock, 'GET_DETECTIONS', {'limite': 100})
    print("📤 Solicitando historial...")

    # Recibir respuesta
    resp = recibir_mensaje(sock)
    if resp and resp['tipo'] == 'ACK':
        detecciones = resp['datos'].get('detecciones', [])
        print(f"✅ Recibidas {len(detecciones)} detecciones")

        if detecciones:
            print("\nPrimeras 3 detecciones:")
            for i, det in enumerate(detecciones[:3]):
                print(f"  {i+1}. {det['objeto']} - confianza: {det['confianza']:.2f}")
                print(f"     Imagen: {det['imagen_path']}")

    # Suscribirse a actualizaciones
    enviar_mensaje(sock, 'SUBSCRIBE_UPDATES', {})
    print("\n📤 Suscrito a actualizaciones en tiempo real")
    print("Esperando nuevas detecciones... (Ctrl+C para salir)")

    # Recibir actualizaciones
    while True:
        msg = recibir_mensaje(sock)
        if not msg:
            print("❌ Servidor desconectado")
            break

        if msg['tipo'] == 'DETECTION':
            det = msg['datos']
            print(f"\n🔔 Nueva detección: {det['objeto']} ({det['confianza']:.2f})")
            print(f"   Imagen: {det['imagen_path']}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSaliendo...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
