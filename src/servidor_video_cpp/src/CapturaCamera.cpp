#include "CapturaCamera.h"
#include "Protocolo.h"
#include <iostream>
#include <chrono>
#include <thread>

// FrameQueue implementation
void FrameQueue::agregar(const Frame& frame) {
    std::lock_guard<std::mutex> lock(mtx);

    cola.push(frame);

    // Limitar tamaño
    while (cola.size() > maxSize) {
        cola.pop();
    }
}

bool FrameQueue::obtener(Frame& frame) {
    std::lock_guard<std::mutex> lock(mtx);

    if (cola.empty()) {
        return false;
    }

    frame = cola.front();
    cola.pop();
    return true;
}

bool FrameQueue::tieneFrames() const {
    std::lock_guard<std::mutex> lock(mtx);
    return !cola.empty();
}

size_t FrameQueue::tamano() const {
    std::lock_guard<std::mutex> lock(mtx);
    return cola.size();
}

// CapturaCamera implementation
CapturaCamera::CapturaCamera(const json& config, FrameQueue* queue,
                             int resize_w, int resize_h, int qual)
    : frameQueue(queue), resizeWidth(resize_w), resizeHeight(resize_h), quality(qual) {

    cameraId = config["id"];
    nombre = config["nombre"];
    rtspUrl = config["rtsp_url"];
    fps = config.value("fps", 30);
}

CapturaCamera::~CapturaCamera() {
    detener();
}

void CapturaCamera::iniciar() {
    if (ejecutando) {
        return;
    }

    ejecutando = true;
    hiloCaptura = std::thread(&CapturaCamera::ejecutar, this);
}

void CapturaCamera::detener() {
    if (!ejecutando) {
        return;
    }

    ejecutando = false;

    if (hiloCaptura.joinable()) {
        hiloCaptura.join();
    }

    if (capture.isOpened()) {
        capture.release();
    }
}

void CapturaCamera::ejecutar() {
    std::cout << "[Cámara " << cameraId << "] Iniciando captura: " << nombre << std::endl;

    // Validar URL
    if (rtspUrl.find("(COLOCAR_AQUI") != std::string::npos) {
        std::cerr << "[Cámara " << cameraId << "] ERROR: URL RTSP no configurada" << std::endl;
        std::cerr << "  Por favor editar config/config.json y colocar URL RTSP válida" << std::endl;
        std::cerr << "  Formato: rtsp://usuario:password@IP:puerto/stream" << std::endl;
        return;
    }

    // Intentar abrir cámara
    capture.open(rtspUrl);

    if (!capture.isOpened()) {
        std::cerr << "[Cámara " << cameraId << "] ERROR: No se pudo conectar a " << rtspUrl << std::endl;
        return;
    }

    std::cout << "[Cámara " << cameraId << "] Conexión exitosa" << std::endl;

    // Calcular delay entre frames
    double frameDelay = 1.0 / fps;

    cv::Mat frame;
    errores = 0;

    while (ejecutando) {
        auto inicio = std::chrono::steady_clock::now();

        bool ret = capture.read(frame);

        if (!ret || frame.empty()) {
            std::cerr << "[Cámara " << cameraId << "] Error leyendo frame" << std::endl;
            errores++;

            // Si hay muchos errores, intentar reconectar
            if (errores > 10) {
                std::cout << "[Cámara " << cameraId << "] Demasiados errores, reconectando..." << std::endl;
                capture.release();
                std::this_thread::sleep_for(std::chrono::seconds(2));
                capture.open(rtspUrl);
                errores = 0;
            }

            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            continue;
        }

        errores = 0;

        // Redimensionar frame
        cv::Mat frameResized;
        cv::resize(frame, frameResized, cv::Size(resizeWidth, resizeHeight));

        // Agregar a cola
        Frame frameData;
        frameData.cameraId = cameraId;
        frameData.imagen = frameResized.clone();
        frameData.timestamp = Protocolo::obtenerTimestamp();

        frameQueue->agregar(frameData);
        framesCapturados++;

        // Controlar FPS
        auto fin = std::chrono::steady_clock::now();
        auto duracion = std::chrono::duration<double>(fin - inicio).count();
        double tiempoEspera = frameDelay - duracion;

        if (tiempoEspera > 0) {
            std::this_thread::sleep_for(
                std::chrono::duration<double>(tiempoEspera)
            );
        }
    }

    if (capture.isOpened()) {
        capture.release();
    }

    std::cout << "[Cámara " << cameraId << "] Captura detenida" << std::endl;
}
