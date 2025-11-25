#include "ConfigLoader.h"
#include <fstream>
#include <iostream>

json ConfigLoader::cargarConfig(const std::string& ruta) {
    try {
        std::ifstream archivo(ruta);

        if (!archivo.is_open()) {
            std::cerr << "Error: No se encontró el archivo de configuración en " << ruta << std::endl;
            return json();
        }

        json config;
        archivo >> config;

        return config;

    } catch (const std::exception& e) {
        std::cerr << "Error al parsear JSON: " << e.what() << std::endl;
        return json();
    }
}

json ConfigLoader::obtenerCamaras(const json& config) {
    json camarasHabilitadas = json::array();

    if (!config.contains("camaras") || !config["camaras"].contains("lista")) {
        return camarasHabilitadas;
    }

    const json& lista = config["camaras"]["lista"];

    for (const auto& camara : lista) {
        if (camara.value("enabled", true)) {
            camarasHabilitadas.push_back(camara);
        }
    }

    return camarasHabilitadas;
}

bool ConfigLoader::validarRtspUrl(const std::string& url) {
    if (url.find("(COLOCAR_AQUI") != std::string::npos) {
        return false;
    }

    if (url.substr(0, 7) != "rtsp://") {
        return false;
    }

    return true;
}
