#!/usr/bin/env python3
# ─────────────────────────────────────────
# dashboard.py
# Panel de control visual con curses
# ─────────────────────────────────────────

import curses
import threading
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import DISPOSITIVOS, PUERTO_SERIE, BAUDRATE
import firebase_client as fb
import serial_client as serie

# ─────────────────────────────────────────
# Estado global
estado = {
    "sensor": {"temperatura": "-", "humedad": "-", "timestamp": "-"},
    "firebase": {"ok": False, "ultimo_arranque": "-", "version": "-"},
    "usb": {"conectado": False, "puerto": "-"},
    "web": {"ip": "-", "modo": "-", "red": "-"},
    "monitor": [],
    "corriendo": True
}

MAX_LINEAS_MONITOR = 20

# ─────────────────────────────────────────
def hilo_firebase():
    while estado["corriendo"]:
        try:
            dispositivo = DISPOSITIVOS["dht11_esp32"]
            lectura = fb.obtener_ultima_lectura(dispositivo["ruta_sensores"])
            if lectura:
                estado["sensor"]["temperatura"] = str(lectura.get("temperatura", "-"))
                estado["sensor"]["humedad"]      = str(lectura.get("humedad", "-"))
                estado["sensor"]["timestamp"]    = lectura.get("timestamp", "-")
                estado["firebase"]["ok"] = True

            est = fb.obtener_estado_dispositivo("dht11_esp32")
            if est:
                estado["web"]["ip"]   = est.get("ip", "-")
                estado["web"]["modo"] = est.get("modo", "-")
                estado["web"]["red"]  = est.get("red", "-")
                estado["firebase"]["ultimo_arranque"] = est.get("ultimo_arranque", "-")
                estado["firebase"]["version"]         = est.get("version", "-")
        except:
            estado["firebase"]["ok"] = False
        time.sleep(30)

# ─────────────────────────────────────────
def hilo_serie():
    while estado["corriendo"]:
        if serie.conectar():
            estado["usb"]["conectado"] = True
            estado["usb"]["puerto"]    = PUERTO_SERIE
            try:
                while estado["corriendo"] and serie.esta_conectado():
                    import serial
                    if serie._serial.in_waiting:
                        linea = serie._serial.readline().decode("utf-8", errors="ignore").strip()
                        if linea:
                            estado["monitor"].append(linea)
                            if len(estado["monitor"]) > MAX_LINEAS_MONITOR:
                                estado["monitor"].pop(0)
                    time.sleep(0.05)
            except:
                pass
            serie.desconectar()
        estado["usb"]["conectado"] = False
        estado["usb"]["puerto"]    = "-"
        time.sleep(5)

# ─────────────────────────────────────────
def dibujar_recuadro(win, y, x, h, w, titulo=""):
    win.attron(curses.color_pair(3))
    win.addstr(y,   x,   "╔" + "═" * (w-2) + "╗")
    for i in range(1, h-1):
        win.addstr(y+i, x, "║")
        win.addstr(y+i, x+w-1, "║")
    win.addstr(y+h-1, x, "╚" + "═" * (w-2) + "╝")
    if titulo:
        win.attron(curses.color_pair(4))
        win.addstr(y, x+2, f" {titulo} ")
    win.attroff(curses.color_pair(4))
    win.attroff(curses.color_pair(3))

# ─────────────────────────────────────────
def dibujar_panel(win):
    win.erase()
    alto, ancho = win.getmaxyx()

    # Colores
    curses.init_pair(1, curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED,    curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN,   curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_WHITE,  curses.COLOR_BLACK)

    # Título
    titulo = "Agro - Panel de Control"
    win.attron(curses.color_pair(4) | curses.A_BOLD)
    win.addstr(0, (ancho - len(titulo)) // 2, titulo)
    win.attroff(curses.color_pair(4) | curses.A_BOLD)

    # Dimensiones cuadrantes superiores
    ancho_cuad = ancho // 4
    alto_cuad  = 7

    # ── Cuadrante 1: Sensor ──
    dibujar_recuadro(win, 2, 0, alto_cuad, ancho_cuad, "Sensor DHT11")
    win.attron(curses.color_pair(5))
    win.addstr(4, 2, f"Temp : {estado['sensor']['temperatura']} C")
    win.addstr(5, 2, f"Hum  : {estado['sensor']['humedad']} %")
    ts = estado['sensor']['timestamp']
    win.addstr(6, 2, f"Hora : {ts[11:] if len(ts) > 11 else ts}")
    win.attroff(curses.color_pair(5))

    # ── Cuadrante 2: USB ──
    dibujar_recuadro(win, 2, ancho_cuad, alto_cuad, ancho_cuad, "Conexion USB")
    if estado["usb"]["conectado"]:
        win.attron(curses.color_pair(1))
        win.addstr(4, ancho_cuad+2, "● Conectado")
        win.attroff(curses.color_pair(1))
        win.attron(curses.color_pair(5))
        win.addstr(5, ancho_cuad+2, estado["usb"]["puerto"][:ancho_cuad-4])
    else:
        win.attron(curses.color_pair(2))
        win.addstr(4, ancho_cuad+2, "● Sin conexion")
        win.attroff(curses.color_pair(2))
    win.attroff(curses.color_pair(5))

    # ── Cuadrante 3: Web ──
    dibujar_recuadro(win, 2, ancho_cuad*2, alto_cuad, ancho_cuad, "Conexion Web")
    if estado["web"]["ip"] != "-":
        win.attron(curses.color_pair(1))
        win.addstr(4, ancho_cuad*2+2, "● En red")
        win.attroff(curses.color_pair(1))
        win.attron(curses.color_pair(5))
        win.addstr(5, ancho_cuad*2+2, f"IP  : {estado['web']['ip'][:ancho_cuad-8]}")
        win.addstr(6, ancho_cuad*2+2, f"Modo: {estado['web']['modo'][:ancho_cuad-8]}")
    else:
        win.attron(curses.color_pair(2))
        win.addstr(4, ancho_cuad*2+2, "● Sin datos")
        win.attroff(curses.color_pair(2))
    win.attroff(curses.color_pair(5))

    # ── Cuadrante 4: Firebase ──
    dibujar_recuadro(win, 2, ancho_cuad*3, alto_cuad, ancho - ancho_cuad*3, "Firebase")
    if estado["firebase"]["ok"]:
        win.attron(curses.color_pair(1))
        win.addstr(4, ancho_cuad*3+2, "● Conectado")
        win.attroff(curses.color_pair(1))
        win.attron(curses.color_pair(5))
        win.addstr(5, ancho_cuad*3+2, f"v{estado['firebase']['version']}")
        arr = estado['firebase']['ultimo_arranque']
        win.addstr(6, ancho_cuad*3+2, arr[11:] if len(arr) > 11 else arr)
    else:
        win.attron(curses.color_pair(2))
        win.addstr(4, ancho_cuad*3+2, "● Sin datos")
        win.attroff(curses.color_pair(2))
    win.attroff(curses.color_pair(5))

    # ── Monitor Serie ──
    alto_monitor = alto - alto_cuad - 5
    dibujar_recuadro(win, alto_cuad+2, 0, alto_monitor, ancho, "Monitor Serie en vivo (USB)")
    lineas = estado["monitor"][-(alto_monitor-2):]
    for i, linea in enumerate(lineas):
        try:
            win.attron(curses.color_pair(5))
            win.addstr(alto_cuad+3+i, 2, linea[:ancho-4])
            win.attroff(curses.color_pair(5))
        except:
            pass

    # ── Menú inferior ──
    menu = "[H] Historial  [R] Reiniciar  [Q] Salir"
    win.attron(curses.color_pair(4))
    try:
        win.addstr(alto-1, (ancho - len(menu)) // 2, menu)
    except:
        pass
    win.attroff(curses.color_pair(4))

    win.refresh()

# ─────────────────────────────────────────
def mostrar_historial(win):
    win.nodelay(False)  # Esperar tecla
    win.timeout(-1)     # Sin timeout
    win.clear()
    alto, ancho = win.getmaxyx()
    dispositivo = DISPOSITIVOS["dht11_esp32"]
    historial = fb.obtener_historial(dispositivo["ruta_sensores"], 20)

    win.attron(curses.color_pair(4) | curses.A_BOLD)
    win.addstr(0, 2, "Historial de lecturas (ultimas 20)")
    win.attroff(curses.color_pair(4) | curses.A_BOLD)

    win.attron(curses.color_pair(5))
    win.addstr(2, 2, f"{'Fecha':<22} {'Temp':>8} {'Humedad':>10}")
    win.addstr(3, 2, "─" * 44)

    for i, (clave, datos) in enumerate(historial):
        fecha, hora = clave.split("_")
        hora = hora.replace("-", ":")
        ts  = f"{fecha} {hora}"
        tmp = str(datos.get('temperatura', '-')) + " C"
        hum = str(datos.get('humedad', '-')) + " %"
        win.addstr(4+i, 2, f"{ts:<22} {tmp:>8} {hum:>10}")

    win.addstr(alto-1, 2, "Presiona cualquier tecla para volver...")
    win.attroff(curses.color_pair(5))
    win.refresh()
    win.getch()
    win.nodelay(True)   # Volver a modo no bloqueante
    win.timeout(500)


# ─────────────────────────────────────────
def main(win):
    curses.curs_set(0)
    win.nodelay(True)
    win.timeout(500)

    # Iniciar hilos
    t_fb = threading.Thread(target=hilo_firebase, daemon=True)
    t_se = threading.Thread(target=hilo_serie,    daemon=True)
    t_fb.start()
    t_se.start()

    while True:
        try:
            dibujar_panel(win)
            tecla = win.getch()

            if tecla in (ord('q'), ord('Q')):
                estado["corriendo"] = False
                break
            elif tecla in (ord('h'), ord('H')):
                mostrar_historial(win)
            elif tecla in (ord('r'), ord('R')):
                ok = serie.reiniciar_esp32()
                estado["monitor"].append(">> ESP32 reiniciado." if ok else ">> Error al reiniciar.")

        except KeyboardInterrupt:
            estado["corriendo"] = False
            break
        except Exception as e:
            pass

# ─────────────────────────────────────────
if __name__ == "__main__":
    curses.wrapper(main)
