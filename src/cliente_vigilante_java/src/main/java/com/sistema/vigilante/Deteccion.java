package com.sistema.vigilante;

import org.json.JSONObject;
import org.json.JSONArray;

/**
 * Representa una detección de objeto
 */
public class Deteccion {
    private int id;
    private int cameraId;
    private String objeto;
    private double confianza;
    private int[] bbox; // [x1, y1, x2, y2]
    private String imagenPath;
    private String timestamp;
    private String fecha;
    private String hora;

    public Deteccion(JSONObject json) {
        this.id = json.optInt("id", 0);
        this.cameraId = json.optInt("camera_id", 0);
        this.objeto = json.optString("objeto", "Desconocido");
        this.confianza = json.optDouble("confianza", 0.0);

        // Parsear bbox
        if (json.has("bbox")) {
            JSONArray bboxArray = json.getJSONArray("bbox");
            this.bbox = new int[4];
            for (int i = 0; i < 4 && i < bboxArray.length(); i++) {
                this.bbox[i] = bboxArray.getInt(i);
            }
        } else {
            this.bbox = new int[]{0, 0, 0, 0};
        }

        this.imagenPath = json.optString("imagen_path", "");
        this.timestamp = json.optString("timestamp", "");
        this.fecha = json.optString("fecha", "");
        this.hora = json.optString("hora", "");
    }

    // Getters
    public int getId() { return id; }
    public int getCameraId() { return cameraId; }
    public String getObjeto() { return objeto; }
    public double getConfianza() { return confianza; }
    public int[] getBbox() { return bbox; }
    public String getImagenPath() { return imagenPath; }
    public String getTimestamp() { return timestamp; }
    public String getFecha() { return fecha; }
    public String getHora() { return hora; }

    @Override
    public String toString() {
        return String.format("Deteccion[id=%d, objeto=%s, confianza=%.2f, camara=%d]",
                id, objeto, confianza, cameraId);
    }
}
