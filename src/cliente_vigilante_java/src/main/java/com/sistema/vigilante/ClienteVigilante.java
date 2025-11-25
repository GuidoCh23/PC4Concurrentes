package com.sistema.vigilante;

import org.json.JSONObject;
import org.json.JSONArray;
import java.io.*;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Paths;

/**
 * Cliente Vigilante - Sistema de Detección de Objetos
 * Implementado en Java con Swing
 */
public class ClienteVigilante {
    private String servidorHost;
    private int servidorPuerto;
    private int maxRegistros;

    private Socket socket;
    private InputStream input;
    private OutputStream output;
    private boolean conectado = false;
    private boolean ejecutando = false;

    private InterfazGUI gui;
    private Thread hiloReceptor;

    public ClienteVigilante(String configPath) throws IOException {
        cargarConfiguracion(configPath);
    }

    private void cargarConfiguracion(String configPath) throws IOException {
        System.out.println("Cargando configuración desde: " + configPath);

        String contenido = new String(Files.readAllBytes(Paths.get(configPath)));
        JSONObject config = new JSONObject(contenido);

        JSONObject clienteConfig = config.getJSONObject("cliente_vigilante");
        JSONObject testeoConfig = config.getJSONObject("servidor_testeo");

        this.servidorHost = clienteConfig.getString("servidor_testeo_host");
        this.servidorPuerto = clienteConfig.getInt("servidor_testeo_puerto");
        this.maxRegistros = clienteConfig.getInt("max_registros_mostrar");

        // Validar host
        if (servidorHost.contains("(COLOCAR_AQUI")) {
            System.out.println("ADVERTENCIA: Host no configurado, usando localhost");
            this.servidorHost = "127.0.0.1";
        }

        System.out.println("Configuración cargada:");
        System.out.println("  Servidor: " + servidorHost + ":" + servidorPuerto);
        System.out.println("  Max registros: " + maxRegistros);
    }

    public boolean conectar() {
        try {
            System.out.println("Conectando a " + servidorHost + ":" + servidorPuerto + "...");

            socket = new Socket(servidorHost, servidorPuerto);
            input = socket.getInputStream();
            output = socket.getOutputStream();

            System.out.println("✓ Conexión exitosa");

            conectado = true;

            // Solicitar historial de detecciones
            JSONObject datos = new JSONObject();
            datos.put("limite", maxRegistros);
            Protocolo.enviarMensaje(output, Protocolo.GET_DETECTIONS, datos);

            // Suscribirse a actualizaciones
            Protocolo.enviarMensaje(output, Protocolo.SUBSCRIBE_UPDATES, new JSONObject());

            return true;

        } catch (IOException e) {
            System.err.println("✗ Error conectando: " + e.getMessage());
            return false;
        }
    }

    private void recibirActualizaciones() {
        System.out.println("[Receptor] Iniciando recepción de actualizaciones...");

        while (ejecutando && conectado) {
            try {
                JSONObject mensaje = Protocolo.recibirMensaje(input);

                if (mensaje == null) {
                    System.out.println("[Receptor] Servidor desconectado");
                    conectado = false;
                    if (gui != null) {
                        gui.setConectado(false);
                    }
                    break;
                }

                String tipo = mensaje.getString("tipo");
                JSONObject datos = mensaje.getJSONObject("datos");

                switch (tipo) {
                    case Protocolo.DETECTION:
                        // Nueva detección
                        Deteccion deteccion = new Deteccion(datos);
                        System.out.println("[Receptor] Detección recibida: " + deteccion);

                        if (gui != null) {
                            gui.agregarDeteccion(deteccion);
                        }
                        break;

                    case Protocolo.ACK:
                        // Respuesta a GET_DETECTIONS
                        if (datos.has("detecciones")) {
                            JSONArray detecciones = datos.getJSONArray("detecciones");
                            System.out.println("[Receptor] Recibidas " + detecciones.length() +
                                    " detecciones históricas");

                            for (int i = 0; i < detecciones.length(); i++) {
                                JSONObject detObj = detecciones.getJSONObject(i);
                                Deteccion det = new Deteccion(detObj);

                                if (gui != null) {
                                    gui.agregarDeteccion(det);
                                }
                            }
                        }
                        break;

                    default:
                        System.out.println("[Receptor] Mensaje recibido: " + tipo);
                }

            } catch (IOException e) {
                if (ejecutando) {
                    System.err.println("[Receptor] Error: " + e.getMessage());
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException ie) {
                        break;
                    }
                }
            }
        }

        System.out.println("[Receptor] Detenido");
    }

    public void ejecutar() {
        try {
            System.out.println("============================================================");
            System.out.println("CLIENTE VIGILANTE (JAVA)");
            System.out.println("============================================================");

            // Conectar al servidor
            if (!conectar()) {
                System.err.println("\nERROR: No se pudo conectar al servidor");
                System.err.println("  Asegúrate de que el servidor de testeo esté ejecutándose");
                return;
            }

            ejecutando = true;

            // Crear interfaz gráfica
            gui = new InterfazGUI(maxRegistros);
            gui.setConectado(conectado);
            gui.setVisible(true);

            // Iniciar hilo receptor
            hiloReceptor = new Thread(this::recibirActualizaciones);
            hiloReceptor.setDaemon(true);
            hiloReceptor.start();

            System.out.println("\n✓ Sistema iniciado correctamente");
            System.out.println("La interfaz gráfica está abierta");

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public void detener() {
        System.out.println("\n[Cliente] Deteniendo cliente...");

        ejecutando = false;
        conectado = false;

        if (socket != null && !socket.isClosed()) {
            try {
                socket.close();
            } catch (IOException e) {
                // Ignorar
            }
        }

        if (hiloReceptor != null && hiloReceptor.isAlive()) {
            try {
                hiloReceptor.join(2000);
            } catch (InterruptedException e) {
                // Ignorar
            }
        }

        System.out.println("[Cliente] Cliente detenido");
    }

    public static void main(String[] args) {
        String configPath = "config/config.json";

        if (args.length > 0) {
            configPath = args[0];
        }

        try {
            ClienteVigilante cliente = new ClienteVigilante(configPath);

            // Configurar shutdown hook
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("\n[Main] Señal de cierre recibida");
                cliente.detener();
            }));

            cliente.ejecutar();

        } catch (Exception e) {
            System.err.println("Error fatal: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
