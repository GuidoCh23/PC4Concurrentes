#ifndef SERVIDOR_VIDEO_H
#define SERVIDOR_VIDEO_H

#include "CapturaCamera.h"
#include "Protocolo.h"
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

/**
 * Servidor de Video que gestiona múltiples cámaras y clientes
 */
class ServidorVideo {
private:
    json config;
    std::string host;
    int puerto;
    int maxClientes;
    int bufferSize;

    int frameQuality;
    int resizeWidth;
    int resizeHeight;

    int socketServidor = -1;
    std::atomic<bool> ejecutando{false};

    FrameQueue frameQueue;
    std::vector<CapturaCamera*> capturas;

    std::vector<int> clientes;
    std::mutex clientesMutex;

    std::thread hiloAceptar;
    std::thread hiloEnviar;

    // Funciones internas
    void iniciarCapturas();
    void iniciarServidor();
    void aceptarClientes();
    void enviarFrames();

    int contadorFrames = 0;

public:
    explicit ServidorVideo(const std::string& configPath);
    ~ServidorVideo();

    void ejecutar();
    void detener();
};

#endif // SERVIDOR_VIDEO_H
