#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H

#include <string>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

/**
 * Carga configuración desde archivo JSON
 */
class ConfigLoader {
public:
    /**
     * Carga el archivo de configuración
     */
    static json cargarConfig(const std::string& ruta);

    /**
     * Obtiene lista de cámaras habilitadas
     */
    static json obtenerCamaras(const json& config);

    /**
     * Valida URL RTSP
     */
    static bool validarRtspUrl(const std::string& url);
};

#endif // CONFIG_LOADER_H
