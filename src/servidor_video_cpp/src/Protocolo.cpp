#include "Protocolo.h"
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <iostream>

// Base64 implementation
static const std::string base64_chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789+/";

static std::string base64_encode(const std::vector<uint8_t>& buf) {
    std::string ret;
    int i = 0;
    int j = 0;
    uint8_t char_array_3[3];
    uint8_t char_array_4[4];
    size_t buf_len = buf.size();
    const uint8_t* bytes_to_encode = buf.data();

    while (buf_len--) {
        char_array_3[i++] = *(bytes_to_encode++);
        if (i == 3) {
            char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
            char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
            char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
            char_array_4[3] = char_array_3[2] & 0x3f;

            for(i = 0; i < 4; i++)
                ret += base64_chars[char_array_4[i]];
            i = 0;
        }
    }

    if (i) {
        for(j = i; j < 3; j++)
            char_array_3[j] = '\0';

        char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
        char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
        char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);

        for (j = 0; j < i + 1; j++)
            ret += base64_chars[char_array_4[j]];

        while((i++ < 3))
            ret += '=';
    }

    return ret;
}

json Protocolo::crearMensaje(const std::string& tipo, const json& datos) {
    json mensaje;
    mensaje["tipo"] = tipo;
    mensaje["timestamp"] = obtenerTimestamp();
    mensaje["datos"] = datos;
    return mensaje;
}

std::vector<uint8_t> Protocolo::serializar(const json& mensaje) {
    // Convertir JSON a string
    std::string mensajeStr = mensaje.dump();

    // Crear vector para header + body
    std::vector<uint8_t> resultado;

    // Tamaño del mensaje en big-endian (4 bytes)
    uint32_t tamano = static_cast<uint32_t>(mensajeStr.size());
    uint32_t tamanoNetworkOrder = htonl(tamano);

    // Agregar header
    uint8_t* header = reinterpret_cast<uint8_t*>(&tamanoNetworkOrder);
    resultado.insert(resultado.end(), header, header + HEADER_SIZE);

    // Agregar body
    resultado.insert(resultado.end(), mensajeStr.begin(), mensajeStr.end());

    return resultado;
}

bool Protocolo::enviarMensaje(int socket, const std::string& tipo, const json& datos) {
    try {
        json mensaje = crearMensaje(tipo, datos);
        std::vector<uint8_t> mensajeBytes = serializar(mensaje);

        ssize_t enviados = send(socket, mensajeBytes.data(), mensajeBytes.size(), 0);

        if (enviados < 0) {
            std::cerr << "Error enviando mensaje: " << strerror(errno) << std::endl;
            return false;
        }

        return true;
    } catch (const std::exception& e) {
        std::cerr << "Excepción enviando mensaje: " << e.what() << std::endl;
        return false;
    }
}

json Protocolo::recibirMensaje(int socket) {
    try {
        // Recibir header (4 bytes)
        std::vector<uint8_t> header = recibirExacto(socket, HEADER_SIZE);

        if (header.empty()) {
            return json();  // Retornar JSON vacío si no hay datos
        }

        // Extraer tamaño
        uint32_t tamanoNetworkOrder;
        std::memcpy(&tamanoNetworkOrder, header.data(), HEADER_SIZE);
        uint32_t tamano = ntohl(tamanoNetworkOrder);

        // Validar tamaño razonable (máximo 100MB)
        if (tamano == 0 || tamano > 100 * 1024 * 1024) {
            std::cerr << "Tamaño de mensaje inválido: " << tamano << std::endl;
            return json();
        }

        // Recibir body
        std::vector<uint8_t> body = recibirExacto(socket, tamano);

        if (body.empty()) {
            return json();
        }

        // Convertir a string y parsear JSON
        std::string mensajeStr(body.begin(), body.end());
        json mensaje = json::parse(mensajeStr);

        return mensaje;

    } catch (const std::exception& e) {
        std::cerr << "Error recibiendo mensaje: " << e.what() << std::endl;
        return json();
    }
}

std::vector<uint8_t> Protocolo::recibirExacto(int socket, size_t n_bytes) {
    std::vector<uint8_t> datos(n_bytes);
    size_t recibidos = 0;

    while (recibidos < n_bytes) {
        ssize_t resultado = recv(socket, datos.data() + recibidos,
                                n_bytes - recibidos, 0);

        if (resultado <= 0) {
            if (resultado == 0) {
                // Conexión cerrada
                return std::vector<uint8_t>();
            } else {
                // Error
                std::cerr << "Error en recv: " << strerror(errno) << std::endl;
                return std::vector<uint8_t>();
            }
        }

        recibidos += resultado;
    }

    return datos;
}

bool Protocolo::enviarAck(int socket, const std::string& mensaje_id) {
    json datos;
    datos["status"] = "ok";

    if (!mensaje_id.empty()) {
        datos["mensaje_id"] = mensaje_id;
    }

    return enviarMensaje(socket, ACK, datos);
}

bool Protocolo::enviarError(int socket, const std::string& error) {
    json datos;
    datos["error"] = error;
    return enviarMensaje(socket, ERROR, datos);
}

std::string Protocolo::frameABase64(const std::vector<uint8_t>& buffer) {
    return base64_encode(buffer);
}

std::string Protocolo::obtenerTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t_now = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;

    std::stringstream ss;
    ss << std::put_time(std::gmtime(&time_t_now), "%Y-%m-%dT%H:%M:%S");
    ss << '.' << std::setfill('0') << std::setw(3) << ms.count();

    return ss.str();
}
