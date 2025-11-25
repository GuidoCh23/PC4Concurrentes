#include "ServidorVideo.h"
#include "ConfigLoader.h"
#include <iostream>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <csignal>

ServidorVideo::ServidorVideo(const std::string& configPath)
    : frameQueue(100) {

    // Cargar configuración
    config = ConfigLoader::cargarConfig(configPath);

    if (config.empty()) {
        throw std::runtime_error("No se pudo cargar la configuración");
    }

    // Configuración del servidor
    host = config["servidor_video"]["host"];
    puerto = config["servidor_video"]["puerto"];
    maxClientes = config["servidor_video"]["max_clientes"];
    bufferSize = config["servidor_video"]["buffer_size"];

    // Configuración de frames
    frameQuality = config["servidor_video"]["frame_quality"];
    resizeWidth = config["servidor_video"]["resize_width"];
    resizeHeight = config["servidor_video"]["resize_height"];

    std::cout << "Configuración cargada" << std::endl;
}

ServidorVideo::~ServidorVideo() {
    detener();
}

void ServidorVideo::iniciarCapturas() {
    std::cout << "\n=== Iniciando captura de cámaras ===" << std::endl;

    json camaras = ConfigLoader::obtenerCamaras(config);

    std::cout << "Cámaras configuradas: " << camaras.size() << std::endl;

    for (const auto& camConfig : camaras) {
        auto* captura = new CapturaCamera(
            camConfig,
            &frameQueue,
            resizeWidth,
            resizeHeight,
            frameQuality
        );

        captura->iniciar();
        capturas.push_back(captura);
    }

    std::cout << "Total de cámaras iniciadas: " << capturas.size() << "\n" << std::endl;
}

void ServidorVideo::iniciarServidor() {
    std::cout << "\n=== Servidor de Video ===" << std::endl;
    std::cout << "Iniciando servidor en " << host << ":" << puerto << std::endl;

    // Crear socket TCP
    socketServidor = socket(AF_INET, SOCK_STREAM, 0);

    if (socketServidor < 0) {
        throw std::runtime_error("Error creando socket: " + std::string(strerror(errno)));
    }

    // Configurar socket para reutilizar dirección
    int opt = 1;
    if (setsockopt(socketServidor, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        close(socketServidor);
        throw std::runtime_error("Error en setsockopt: " + std::string(strerror(errno)));
    }

    // Configurar dirección
    struct sockaddr_in direccion;
    std::memset(&direccion, 0, sizeof(direccion));
    direccion.sin_family = AF_INET;
    direccion.sin_port = htons(puerto);

    if (host == "0.0.0.0") {
        direccion.sin_addr.s_addr = INADDR_ANY;
    } else {
        inet_pton(AF_INET, host.c_str(), &direccion.sin_addr);
    }

    // Bind
    if (bind(socketServidor, (struct sockaddr*)&direccion, sizeof(direccion)) < 0) {
        close(socketServidor);
        throw std::runtime_error("Error en bind: " + std::string(strerror(errno)));
    }

    // Listen
    if (listen(socketServidor, maxClientes) < 0) {
        close(socketServidor);
        throw std::runtime_error("Error en listen: " + std::string(strerror(errno)));
    }

    std::cout << "Servidor escuchando en puerto " << puerto << std::endl;
    std::cout << "Esperando conexiones...\n" << std::endl;

    ejecutando = true;

    // Iniciar hilos
    hiloAceptar = std::thread(&ServidorVideo::aceptarClientes, this);
    hiloEnviar = std::thread(&ServidorVideo::enviarFrames, this);
}

void ServidorVideo::aceptarClientes() {
    while (ejecutando) {
        struct sockaddr_in clienteAddr;
        socklen_t clienteLen = sizeof(clienteAddr);

        int clienteSocket = accept(socketServidor, (struct sockaddr*)&clienteAddr, &clienteLen);

        if (clienteSocket < 0) {
            if (ejecutando) {
                std::cerr << "[Servidor] Error aceptando cliente: " << strerror(errno) << std::endl;
            }
            continue;
        }

        char clienteIP[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &clienteAddr.sin_addr, clienteIP, INET_ADDRSTRLEN);

        std::cout << "[Servidor] Nueva conexión: " << clienteIP << ":" << ntohs(clienteAddr.sin_port) << std::endl;

        std::lock_guard<std::mutex> lock(clientesMutex);
        clientes.push_back(clienteSocket);
    }
}

void ServidorVideo::enviarFrames() {
    while (ejecutando) {
        Frame frame;

        if (!frameQueue.obtener(frame)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            continue;
        }

        // Codificar frame a JPEG
        std::vector<uchar> buffer;
        std::vector<int> params = {cv::IMWRITE_JPEG_QUALITY, frameQuality};

        if (!cv::imencode(".jpg", frame.imagen, buffer, params)) {
            std::cerr << "[Servidor] Error codificando frame" << std::endl;
            continue;
        }

        // Convertir a base64
        std::string frameBase64 = Protocolo::frameABase64(buffer);

        // Crear mensaje
        json datos;
        datos["camera_id"] = frame.cameraId;
        datos["frame_data"] = frameBase64;
        datos["timestamp"] = frame.timestamp;

        json mensaje = Protocolo::crearMensaje(Protocolo::FRAME, datos);
        std::vector<uint8_t> mensajeBytes = Protocolo::serializar(mensaje);

        // Enviar a todos los clientes
        std::lock_guard<std::mutex> lock(clientesMutex);
        std::vector<int> clientesDesconectados;

        for (int clienteSocket : clientes) {
            ssize_t enviados = send(clienteSocket, mensajeBytes.data(),
                                   mensajeBytes.size(), MSG_NOSIGNAL);

            if (enviados < 0) {
                std::cerr << "[Servidor] Error enviando a cliente" << std::endl;
                clientesDesconectados.push_back(clienteSocket);
            }
        }

        // Eliminar clientes desconectados
        for (int socket : clientesDesconectados) {
            clientes.erase(
                std::remove(clientes.begin(), clientes.end(), socket),
                clientes.end()
            );
            close(socket);
        }

        // Estadísticas
        contadorFrames++;
        if (contadorFrames % 100 == 0) {
            std::cout << "[Servidor] Frames enviados: " << contadorFrames
                     << " | Clientes conectados: " << clientes.size() << std::endl;
        }
    }
}

void ServidorVideo::detener() {
    if (!ejecutando) {
        return;
    }

    std::cout << "\n[Servidor] Deteniendo servidor..." << std::endl;

    ejecutando = false;

    // Detener capturas
    for (auto* captura : capturas) {
        captura->detener();
        delete captura;
    }
    capturas.clear();

    // Cerrar clientes
    {
        std::lock_guard<std::mutex> lock(clientesMutex);
        for (int socket : clientes) {
            close(socket);
        }
        clientes.clear();
    }

    // Cerrar socket servidor
    if (socketServidor >= 0) {
        close(socketServidor);
        socketServidor = -1;
    }

    // Esperar hilos
    if (hiloAceptar.joinable()) {
        hiloAceptar.join();
    }

    if (hiloEnviar.joinable()) {
        hiloEnviar.join();
    }

    std::cout << "[Servidor] Servidor detenido" << std::endl;
}

void ServidorVideo::ejecutar() {
    try {
        // Iniciar capturas
        iniciarCapturas();

        // Iniciar servidor
        iniciarServidor();

        // Mantener ejecutando
        std::cout << "Servidor ejecutándose. Presione Ctrl+C para detener.\n" << std::endl;

        while (ejecutando) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        detener();
    }
}
