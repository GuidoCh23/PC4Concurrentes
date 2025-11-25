# Makefile para Servidor de Video C++
# Alternativa a CMake

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -pthread -Iinclude
LDFLAGS = -pthread

# OpenCV
OPENCV_FLAGS = $(shell pkg-config --cflags opencv4 2>/dev/null || pkg-config --cflags opencv)
OPENCV_LIBS = $(shell pkg-config --libs opencv4 2>/dev/null || pkg-config --libs opencv)

# JSON (nlohmann/json debe estar instalado)
# Ubuntu/Debian: sudo apt install nlohmann-json3-dev
# Fedora: sudo dnf install json-devel
# macOS: brew install nlohmann-json

CXXFLAGS += $(OPENCV_FLAGS)
LDFLAGS += $(OPENCV_LIBS)

# Archivos fuente
SOURCES = src/main.cpp \
          src/ServidorVideo.cpp \
          src/CapturaCamera.cpp \
          src/Protocolo.cpp \
          src/ConfigLoader.cpp

OBJECTS = $(SOURCES:.cpp=.o)
TARGET = servidor_video

# Reglas
all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) $(LDFLAGS) -o $(TARGET)
	@echo ""
	@echo "Compilación exitosa!"
	@echo "Ejecutar con: ./$(TARGET)"
	@echo ""

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)
	@echo "Archivos limpiados"

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run
