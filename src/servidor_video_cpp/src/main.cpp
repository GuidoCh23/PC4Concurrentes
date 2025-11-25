#include "ServidorVideo.h"
#include <iostream>
#include <csignal>
#include <memory>

// Variable global para manejo de señales
std::unique_ptr<ServidorVideo> g_servidor;

void signal_handler(int signal) {
    std::cout << "\n[Main] Señal recibida: " << signal << std::endl;

    if (g_servidor) {
        g_servidor->detener();
    }

    exit(0);
}

int main(int argc, char* argv[]) {
    std::cout << "============================================================" << std::endl;
    std::cout << "SERVIDOR DE VIDEO (C++) - Sistema Distribuido" << std::endl;
    std::cout << "============================================================" << std::endl;

    // Configurar manejo de señales
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Ruta al config
    std::string configPath = "config/config.json";

    if (argc > 1) {
        configPath = argv[1];
    }

    try {
        g_servidor = std::make_unique<ServidorVideo>(configPath);
        g_servidor->ejecutar();

    } catch (const std::exception& e) {
        std::cerr << "Error fatal: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
