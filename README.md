# Agro Panel

Panel de control para el proyecto Agro de monitoreo agrícola-ganadero.

## Descripción

Herramienta de línea de comandos para monitorear y controlar los sensores
del proyecto Agro. Se conecta al ESP32 por USB, por la red local y consulta
datos de Firebase Realtime Database.

## Funciones

- Ver estado del dispositivo (modo, red WiFi, IP, último arranque)
- Ver última lectura del sensor
- Ver historial de lecturas
- Monitor serie en vivo (conexión USB)
- Reiniciar ESP32 (conexión USB)

## Tecnologías

- Python 3
- Firebase Realtime Database
- Puerto serie USB

## Repositorios relacionados

- [campo-sensores](https://github.com/figueiromariano/campo-sensores)
- [agente-campo](https://github.com/figueiromariano/agente-campo)

## Instalación

Clonar el repositorio:

    git clone https://github.com/figueiromariano/agro-panel.git
    cd agro-panel

Instalar dependencias:

    pip3 install firebase-admin pyserial requests --break-system-packages

Copiar y completar la configuración:

    cp src/config.py.ejemplo src/config.py

Editar src/config.py con tus credenciales de Firebase.

## Uso

    python3 panel/panel.py

## Estado

En desarrollo
