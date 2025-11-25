#ifndef CAPTURA_CAMERA_H
#define CAPTURA_CAMERA_H

#include <opencv2/opencv.hpp>
#include <thread>
#include <atomic>
#include <queue>
#include <mutex>
#include <string>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

/**
 * Estructura para almacenar frames en la cola
 */
struct Frame {
    int cameraId;
    cv::Mat imagen;
    std::string timestamp;
};

/**
 * Cola thread-safe para frames
 */
class FrameQueue {
private:
    std::queue<Frame> cola;
    std::mutex mtx;
    size_t maxSize;

public:
    explicit FrameQueue(size_t max_size = 100) : maxSize(max_size) {}

    void agregar(const Frame& frame);
    bool obtener(Frame& frame);
    bool tieneFrames() const;
    size_t tamano() const;
};

/**
 * Hilo que captura frames de una cámara RTSP
 */
class CapturaCamera {
private:
    int cameraId;
    std::string nombre;
    std::string rtspUrl;
    int fps;

    int resizeWidth;
    int resizeHeight;
    int quality;

    std::thread hiloCaptura;
    std::atomic<bool> ejecutando{false};

    cv::VideoCapture capture;
    FrameQueue* frameQueue;

    int framesCapturados = 0;
    int errores = 0;

    // Función del hilo
    void ejecutar();

public:
    CapturaCamera(const json& config, FrameQueue* queue,
                  int resize_w, int resize_h, int qual);

    ~CapturaCamera();

    // Iniciar captura
    void iniciar();

    // Detener captura
    void detener();

    // Getters
    int getCameraId() const { return cameraId; }
    std::string getNombre() const { return nombre; }
    int getFramesCapturados() const { return framesCapturados; }
};

#endif // CAPTURA_CAMERA_H
