package com.sistema.vigilante;

import javax.swing.*;
import javax.swing.table.DefaultTableCellRenderer;
import java.awt.*;
import java.awt.event.*;
import java.io.File;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;

/**
 * Interfaz gráfica del Cliente Vigilante
 */
public class InterfazGUI extends JFrame {
    private DeteccionTableModel tableModel;
    private JTable tabla;
    private JLabel imagenLabel;
    private JLabel statusLabel;
    private JLabel statsLabel;
    private boolean conectado;
    private ImageIcon imagenActual;

    public InterfazGUI(int maxRegistros) {
        this.conectado = false;

        configurarVentana();
        crearComponentes(maxRegistros);
        configurarEventos();
    }

    private void configurarVentana() {
        setTitle("Cliente Vigilante - Sistema de Detección de Objetos");
        setSize(1200, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
    }

    private void crearComponentes(int maxRegistros) {
        // Panel principal
        JPanel mainPanel = new JPanel(new BorderLayout(10, 10));
        mainPanel.setBackground(new Color(43, 43, 43));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Header
        JPanel headerPanel = crearHeader();
        mainPanel.add(headerPanel, BorderLayout.NORTH);

        // Content (tabla + imagen)
        JPanel contentPanel = crearContent(maxRegistros);
        mainPanel.add(contentPanel, BorderLayout.CENTER);

        // Footer (botones)
        JPanel footerPanel = crearFooter();
        mainPanel.add(footerPanel, BorderLayout.SOUTH);

        add(mainPanel);
    }

    private JPanel crearHeader() {
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(new Color(30, 30, 30));
        header.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(Color.DARK_GRAY, 2),
                BorderFactory.createEmptyBorder(10, 10, 10, 10)
        ));

        // Título
        JLabel titleLabel = new JLabel("🎥 SISTEMA DE VIGILANCIA - DETECCIONES EN TIEMPO REAL");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 18));
        titleLabel.setForeground(new Color(0, 255, 0));
        titleLabel.setHorizontalAlignment(SwingConstants.CENTER);
        header.add(titleLabel, BorderLayout.CENTER);

        // Status bar
        JPanel statusPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        statusPanel.setBackground(new Color(30, 30, 30));

        statusLabel = new JLabel("○ Desconectado");
        statusLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        statusLabel.setForeground(Color.RED);
        statusPanel.add(statusLabel);

        statsLabel = new JLabel("Detecciones: 0");
        statsLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        statsLabel.setForeground(Color.WHITE);
        statsLabel.setBorder(BorderFactory.createEmptyBorder(0, 20, 0, 0));
        statusPanel.add(statsLabel);

        header.add(statusPanel, BorderLayout.SOUTH);

        return header;
    }

    private JPanel crearContent(int maxRegistros) {
        JPanel content = new JPanel(new BorderLayout(5, 0));
        content.setBackground(new Color(43, 43, 43));

        // Panel izquierdo: Tabla
        JPanel leftPanel = new JPanel(new BorderLayout());
        leftPanel.setBackground(new Color(43, 43, 43));

        JLabel tablaLabel = new JLabel("HISTORIAL DE DETECCIONES");
        tablaLabel.setFont(new Font("Arial", Font.BOLD, 14));
        tablaLabel.setForeground(Color.WHITE);
        tablaLabel.setBorder(BorderFactory.createEmptyBorder(0, 0, 5, 0));
        leftPanel.add(tablaLabel, BorderLayout.NORTH);

        // Crear tabla
        tableModel = new DeteccionTableModel(maxRegistros);
        tabla = new JTable(tableModel);

        // Configurar apariencia de la tabla
        tabla.setBackground(new Color(30, 30, 30));
        tabla.setForeground(Color.WHITE);
        tabla.setGridColor(new Color(60, 60, 60));
        tabla.setSelectionBackground(new Color(0, 120, 215));
        tabla.setSelectionForeground(Color.WHITE);
        tabla.setFont(new Font("Arial", Font.PLAIN, 12));
        tabla.setRowHeight(25);
        tabla.getTableHeader().setBackground(new Color(20, 20, 20));
        tabla.getTableHeader().setForeground(Color.WHITE);
        tabla.getTableHeader().setFont(new Font("Arial", Font.BOLD, 12));

        // Centrar contenido de celdas
        DefaultTableCellRenderer centerRenderer = new DefaultTableCellRenderer();
        centerRenderer.setHorizontalAlignment(JLabel.CENTER);
        for (int i = 0; i < tabla.getColumnCount(); i++) {
            tabla.getColumnModel().getColumn(i).setCellRenderer(centerRenderer);
        }

        // Ajustar ancho de columnas
        tabla.getColumnModel().getColumn(0).setPreferredWidth(50);  // ID
        tabla.getColumnModel().getColumn(1).setPreferredWidth(150); // Objeto
        tabla.getColumnModel().getColumn(2).setPreferredWidth(80);  // Cámara
        tabla.getColumnModel().getColumn(3).setPreferredWidth(100); // Confianza
        tabla.getColumnModel().getColumn(4).setPreferredWidth(100); // Fecha
        tabla.getColumnModel().getColumn(5).setPreferredWidth(100); // Hora

        JScrollPane scrollPane = new JScrollPane(tabla);
        scrollPane.setBackground(new Color(30, 30, 30));
        leftPanel.add(scrollPane, BorderLayout.CENTER);

        content.add(leftPanel, BorderLayout.CENTER);

        // Panel derecho: Imagen
        JPanel rightPanel = new JPanel(new BorderLayout());
        rightPanel.setBackground(new Color(30, 30, 30));
        rightPanel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(Color.DARK_GRAY, 2),
                BorderFactory.createEmptyBorder(10, 10, 10, 10)
        ));
        rightPanel.setPreferredSize(new Dimension(450, 0));

        JLabel imagenTitle = new JLabel("IMAGEN DE DETECCIÓN");
        imagenTitle.setFont(new Font("Arial", Font.BOLD, 14));
        imagenTitle.setForeground(Color.WHITE);
        imagenTitle.setHorizontalAlignment(SwingConstants.CENTER);
        rightPanel.add(imagenTitle, BorderLayout.NORTH);

        imagenLabel = new JLabel("<html><center>Seleccione una detección<br>para ver la imagen</center></html>");
        imagenLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        imagenLabel.setForeground(new Color(136, 136, 136));
        imagenLabel.setHorizontalAlignment(SwingConstants.CENTER);
        imagenLabel.setVerticalAlignment(SwingConstants.CENTER);
        rightPanel.add(imagenLabel, BorderLayout.CENTER);

        content.add(rightPanel, BorderLayout.EAST);

        return content;
    }

    private JPanel crearFooter() {
        JPanel footer = new JPanel(new FlowLayout(FlowLayout.LEFT));
        footer.setBackground(new Color(30, 30, 30));
        footer.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(Color.DARK_GRAY, 2),
                BorderFactory.createEmptyBorder(10, 10, 10, 10)
        ));

        // Botón Actualizar
        JButton btnActualizar = new JButton("Actualizar");
        btnActualizar.setFont(new Font("Arial", Font.PLAIN, 12));
        btnActualizar.setBackground(new Color(58, 58, 58));
        btnActualizar.setForeground(Color.WHITE);
        btnActualizar.setFocusPainted(false);
        btnActualizar.addActionListener(e -> actualizarManual());
        footer.add(btnActualizar);

        // Botón Limpiar
        JButton btnLimpiar = new JButton("Limpiar");
        btnLimpiar.setFont(new Font("Arial", Font.PLAIN, 12));
        btnLimpiar.setBackground(new Color(58, 58, 58));
        btnLimpiar.setForeground(Color.WHITE);
        btnLimpiar.setFocusPainted(false);
        btnLimpiar.addActionListener(e -> limpiarTabla());
        footer.add(btnLimpiar);

        return footer;
    }

    private void configurarEventos() {
        // Evento de selección en la tabla
        tabla.getSelectionModel().addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                int selectedRow = tabla.getSelectedRow();
                if (selectedRow >= 0) {
                    Deteccion deteccion = tableModel.getDeteccion(selectedRow);
                    if (deteccion != null) {
                        mostrarImagen(deteccion.getImagenPath());
                    }
                }
            }
        });
    }

    // Métodos públicos
    public void setConectado(boolean conectado) {
        this.conectado = conectado;
        SwingUtilities.invokeLater(() -> {
            if (conectado) {
                statusLabel.setText("● Conectado");
                statusLabel.setForeground(new Color(0, 255, 0));
            } else {
                statusLabel.setText("○ Desconectado");
                statusLabel.setForeground(Color.RED);
            }
        });
    }

    public void agregarDeteccion(Deteccion deteccion) {
        SwingUtilities.invokeLater(() -> {
            tableModel.agregarDeteccion(deteccion);
            actualizarEstadisticas();
        });
    }

    private void actualizarEstadisticas() {
        int total = tableModel.getTotalDetecciones();
        statsLabel.setText("Detecciones: " + total);
    }

    private void mostrarImagen(String imagenPath) {
        try {
            File file = new File(imagenPath);

            if (!file.exists()) {
                imagenLabel.setIcon(null);
                imagenLabel.setText("<html><center>Imagen no encontrada:<br>" + imagenPath + "</center></html>");
                return;
            }

            BufferedImage img = ImageIO.read(file);

            if (img == null) {
                imagenLabel.setIcon(null);
                imagenLabel.setText("Error cargando imagen");
                return;
            }

            // Redimensionar manteniendo aspecto
            int maxWidth = 400;
            int maxHeight = 400;

            double ratio = Math.min((double) maxWidth / img.getWidth(),
                                   (double) maxHeight / img.getHeight());

            int newWidth = (int) (img.getWidth() * ratio);
            int newHeight = (int) (img.getHeight() * ratio);

            Image scaledImg = img.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH);
            imagenActual = new ImageIcon(scaledImg);

            imagenLabel.setIcon(imagenActual);
            imagenLabel.setText("");

        } catch (Exception e) {
            imagenLabel.setIcon(null);
            imagenLabel.setText("<html><center>Error cargando imagen:<br>" + e.getMessage() + "</center></html>");
        }
    }

    private void actualizarManual() {
        // Este método será llamado desde ClienteVigilante
        System.out.println("[GUI] Actualización manual solicitada");
    }

    private void limpiarTabla() {
        tableModel.limpiar();
        imagenLabel.setIcon(null);
        imagenLabel.setText("<html><center>Seleccione una detección<br>para ver la imagen</center></html>");
        actualizarEstadisticas();
    }
}
