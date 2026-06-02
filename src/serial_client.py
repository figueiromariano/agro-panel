# ─────────────────────────────────────────
# serial_client.py
# Comunicación con el ESP32 por puerto serie USB
# ─────────────────────────────────────────

import serial
import serial.tools.list_ports
import threading
import time
from config import PUERTO_SERIE, BAUDRATE

_serial = None
_leyendo = False
_hilo = None

# ─────────────────────────────────────────
def listar_puertos():
    puertos = serial.tools.list_ports.comports()
    return [p.device for p in puertos]

# ─────────────────────────────────────────
def conectar(puerto=None):
    global _serial
    try:
        p = puerto or PUERTO_SERIE
        _serial = serial.Serial(p, BAUDRATE, timeout=1)
        time.sleep(1)
        return True
    except Exception:
        return False

# ─────────────────────────────────────────
def desconectar():
    global _serial, _leyendo
    _leyendo = False
    if _serial and _serial.is_open:
        _serial.close()

# ─────────────────────────────────────────
def esta_conectado():
    return _serial is not None and _serial.is_open

# ─────────────────────────────────────────
def monitor_en_vivo(duracion=30):
    if not esta_conectado():
        if not conectar():
            print("No se pudo conectar al ESP32 por USB")
            return
    print(f"Monitor serie en vivo ({duracion} segundos). Ctrl+C para salir.")
    print("─" * 50)
    inicio = time.time()
    try:
        while time.time() - inicio < duracion:
            if _serial.in_waiting:
                linea = _serial.readline().decode("utf-8", errors="ignore").strip()
                if linea:
                    print(f"  {linea}")
    except KeyboardInterrupt:
        print("\nMonitor detenido.")

# ─────────────────────────────────────────
def reiniciar_esp32():
    if not esta_conectado():
        if not conectar():
            return False
    try:
        _serial.setDTR(False)
        time.sleep(0.1)
        _serial.setDTR(True)
        return True
    except Exception as e:
        return False
