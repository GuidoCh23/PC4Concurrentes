package com.sistema.vigilante;

import javax.swing.table.AbstractTableModel;
import java.util.ArrayList;
import java.util.List;

/**
 * Modelo de tabla para mostrar detecciones
 */
public class DeteccionTableModel extends AbstractTableModel {
    private final String[] columnas = {"ID", "Objeto", "Cámara", "Confianza", "Fecha", "Hora"};
    private final List<Deteccion> detecciones;
    private final int maxRegistros;

    public DeteccionTableModel(int maxRegistros) {
        this.detecciones = new ArrayList<>();
        this.maxRegistros = maxRegistros;
    }

    @Override
    public int getRowCount() {
        return detecciones.size();
    }

    @Override
    public int getColumnCount() {
        return columnas.length;
    }

    @Override
    public String getColumnName(int column) {
        return columnas[column];
    }

    @Override
    public Object getValueAt(int rowIndex, int columnIndex) {
        Deteccion det = detecciones.get(rowIndex);

        switch (columnIndex) {
            case 0: return det.getId();
            case 1: return det.getObjeto();
            case 2: return "Cámara " + det.getCameraId();
            case 3: return String.format("%.2f", det.getConfianza());
            case 4: return det.getFecha();
            case 5: return det.getHora();
            default: return null;
        }
    }

    /**
     * Agrega una detección a la tabla
     */
    public synchronized void agregarDeteccion(Deteccion deteccion) {
        // Agregar al inicio
        detecciones.add(0, deteccion);

        // Limitar tamaño
        while (detecciones.size() > maxRegistros) {
            detecciones.remove(detecciones.size() - 1);
        }

        fireTableDataChanged();
    }

    /**
     * Obtiene una detección por índice de fila
     */
    public synchronized Deteccion getDeteccion(int rowIndex) {
        if (rowIndex >= 0 && rowIndex < detecciones.size()) {
            return detecciones.get(rowIndex);
        }
        return null;
    }

    /**
     * Limpia todas las detecciones
     */
    public synchronized void limpiar() {
        detecciones.clear();
        fireTableDataChanged();
    }

    /**
     * Obtiene el número total de detecciones
     */
    public synchronized int getTotalDetecciones() {
        return detecciones.size();
    }
}
