package com.sistema.vigilante;

import org.json.JSONObject;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.time.Instant;

/**
 * Protocolo de comunicación compatible con Python y C++
 * Formato: [4 bytes tamaño big-endian][N bytes JSON UTF-8]
 */
public class Protocolo {

    // Tipos de mensaje
    public static final String FRAME = "FRAME";
    public static final String DETECTION = "DETECTION";
    public static final String GET_DETECTIONS = "GET_DETECTIONS";
    public static final String SUBSCRIBE_UPDATES = "SUBSCRIBE_UPDATES";
    public static final String ACK = "ACK";
    public static final String ERROR = "ERROR";
    public static final String PING = "PING";
    public static final String PONG = "PONG";

    private static final int HEADER_SIZE = 4;

    /**
     * Crea un mensaje con el formato del protocolo
     */
    public static JSONObject crearMensaje(String tipo, JSONObject datos) {
        JSONObject mensaje = new JSONObject();
        mensaje.put("tipo", tipo);
        mensaje.put("timestamp", Instant.now().toString());
        mensaje.put("datos", datos);
        return mensaje;
    }

    /**
     * Serializa un mensaje JSON a bytes
     */
    public static byte[] serializar(JSONObject mensaje) {
        // Convertir JSON a string y luego a bytes UTF-8
        String mensajeStr = mensaje.toString();
        byte[] mensajeBytes = mensajeStr.getBytes(StandardCharsets.UTF_8);

        // Crear buffer para header + body
        int tamano = mensajeBytes.length;
        ByteBuffer buffer = ByteBuffer.allocate(HEADER_SIZE + tamano);

        // Agregar header (4 bytes big-endian)
        buffer.putInt(tamano);

        // Agregar body
        buffer.put(mensajeBytes);

        return buffer.array();
    }

    /**
     * Envía un mensaje por socket
     */
    public static void enviarMensaje(OutputStream output, String tipo, JSONObject datos)
            throws IOException {
        JSONObject mensaje = crearMensaje(tipo, datos);
        byte[] mensajeBytes = serializar(mensaje);
        output.write(mensajeBytes);
        output.flush();
    }

    /**
     * Recibe un mensaje del socket
     */
    public static JSONObject recibirMensaje(InputStream input) throws IOException {
        // Leer header (4 bytes)
        byte[] header = recibirExacto(input, HEADER_SIZE);

        if (header == null) {
            return null; // Conexión cerrada
        }

        // Extraer tamaño (big-endian)
        ByteBuffer buffer = ByteBuffer.wrap(header);
        int tamano = buffer.getInt();

        // Validar tamaño
        if (tamano <= 0 || tamano > 100 * 1024 * 1024) { // Máximo 100MB
            throw new IOException("Tamaño de mensaje inválido: " + tamano);
        }

        // Leer body
        byte[] body = recibirExacto(input, tamano);

        if (body == null) {
            return null;
        }

        // Convertir a string y parsear JSON
        String mensajeStr = new String(body, StandardCharsets.UTF_8);
        return new JSONObject(mensajeStr);
    }

    /**
     * Recibe exactamente n bytes del input stream
     */
    private static byte[] recibirExacto(InputStream input, int nBytes) throws IOException {
        byte[] datos = new byte[nBytes];
        int recibidos = 0;

        while (recibidos < nBytes) {
            int resultado = input.read(datos, recibidos, nBytes - recibidos);

            if (resultado == -1) {
                // Conexión cerrada
                return null;
            }

            recibidos += resultado;
        }

        return datos;
    }

    /**
     * Envía un ACK
     */
    public static void enviarAck(OutputStream output) throws IOException {
        JSONObject datos = new JSONObject();
        datos.put("status", "ok");
        enviarMensaje(output, ACK, datos);
    }

    /**
     * Envía un error
     */
    public static void enviarError(OutputStream output, String error) throws IOException {
        JSONObject datos = new JSONObject();
        datos.put("error", error);
        enviarMensaje(output, ERROR, datos);
    }
}
