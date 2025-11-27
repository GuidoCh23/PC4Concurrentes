#ifndef PROTOCOLO_H
#define PROTOCOLO_H

#include <string>
#include <vector>
#include <cstdint>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

/**
 * Protocolo de comunicación compatible con la versión Python
 * Formato: [4 bytes tamaño][N bytes JSON]
 */
class Protocolo {
public:
    // Tipos de mensaje
    static constexpr const char* FRAME = "FRAME";
    static constexpr const char* VIDEO_STATUS = "VIDEO_STATUS";
    static constexpr const char* ACK = "ACK";
    static constexpr const char* ERROR = "ERROR";
    static constexpr const char* PING = "PING";
    static constexpr const char* PONG = "PONG";

    /**
     * Crea un mensaje con el formato del protocolo
     */
    static json crearMensaje(const std::string& tipo, const json& datos);

    /**
     * Serializa un mensaje JSON a bytes para enviar
     */
    static std::vector<uint8_t> serializar(const json& mensaje);

    /**
     * Envía un mensaje por socket
     */
    static bool enviarMensaje(int socket, const std::string& tipo, const json& datos);

    /**
     * Recibe un mensaje del socket
     */
    static json recibirMensaje(int socket);

    /**
     * Envía un ACK
     */
    static bool enviarAck(int socket, const std::string& mensaje_id = "");

    /**
     * Envía un error
     */
    static bool enviarError(int socket, const std::string& error);

    /**
     * Codifica imagen a base64
     */
    static std::string frameABase64(const std::vector<uint8_t>& buffer);

    /**
     * Obtiene timestamp ISO 8601
     */
    static std::string obtenerTimestamp();

private:
    static constexpr size_t HEADER_SIZE = 4;

    /**
     * Recibe exactamente n bytes del socket
     */
    static std::vector<uint8_t> recibirExacto(int socket, size_t n_bytes);
};

#endif // PROTOCOLO_H
