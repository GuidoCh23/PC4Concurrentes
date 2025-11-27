#!/bin/bash
# Script para probar si Java puede leer las imágenes

# No hardcode paths
# cd /home/guido/Desktop/PC4concurrentes

# Obtener una imagen reciente
IMAGEN=$(ls -t detecciones/camara_1/*.jpg 2>/dev/null | head -1)

if [ -z "$IMAGEN" ]; then
    echo "❌ No hay imágenes en detecciones/camara_1/"
    # Intento crear un directorio y un archivo dummy si no existen para testear
    mkdir -p detecciones/camara_1/
    touch detecciones/camara_1/test_dummy.jpg
    IMAGEN="detecciones/camara_1/test_dummy.jpg"
    echo "⚠️  Creada imagen dummy para prueba: $IMAGEN"
fi

echo "Probando acceso a imagen:"
echo "  Ruta: $IMAGEN"
echo "  Existe: $(test -f "$IMAGEN" && echo "✅ SÍ" || echo "❌ NO")"
echo "  Tamaño: $(du -h "$IMAGEN" | cut -f1)"
echo "  Permisos: $(ls -lh "$IMAGEN" | awk '{print $1, $3, $4}')"

# Crear programa Java simple para probar
cat > TestImagen.java <<'JAVA'
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;

public class TestImagen {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Uso: java TestImagen <ruta_imagen>");
            return;
        }

        String ruta = args[0];
        System.out.println("Probando cargar imagen: " + ruta);

        File file = new File(ruta);
        System.out.println("Ruta absoluta: " + file.getAbsolutePath());
        System.out.println("Existe: " + file.exists());
        System.out.println("Es archivo: " + file.isFile());
        System.out.println("Se puede leer: " + file.canRead());

        if (file.exists()) {
            try {
                BufferedImage img = ImageIO.read(file);
                if (img != null) {
                    System.out.println("✅ Imagen cargada exitosamente");
                    System.out.println("   Dimensiones: " + img.getWidth() + "x" + img.getHeight());
                } else {
                    System.out.println("❌ ImageIO.read() retornó null (posiblemente no es una imagen válida o dummy vacía)");
                }
            } catch (Exception e) {
                System.out.println("❌ Error cargando imagen: " + e.getMessage());
                e.printStackTrace();
            }
        }
    }
}
JAVA

javac TestImagen.java
java TestImagen "$IMAGEN"

# Limpiar
rm -f TestImagen.java TestImagen.class

echo ""
echo "Si el test anterior funcionó, el problema está en el path del cliente Java"
