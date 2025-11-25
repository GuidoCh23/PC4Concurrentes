cmake_minimum_required(VERSION 3.10)
project(ServidorVideo)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Buscar OpenCV
find_package(OpenCV REQUIRED)

# Buscar nlohmann/json (JSON para C++)
find_package(nlohmann_json 3.2.0 REQUIRED)

# Incluir directorios
include_directories(${OpenCV_INCLUDE_DIRS})
include_directories(include)

# Archivos fuente
set(SOURCES
    src/main.cpp
    src/ServidorVideo.cpp
    src/CapturaCamera.cpp
    src/Protocolo.cpp
    src/ConfigLoader.cpp
)

# Ejecutable
add_executable(servidor_video ${SOURCES})

# Enlazar librerías
target_link_libraries(servidor_video
    ${OpenCV_LIBS}
    nlohmann_json::nlohmann_json
    pthread
)

# Flags de compilación
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
