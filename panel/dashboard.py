#!/usr/bin/env python3
import fcntl

# Verificar instancia unica
lock_file = open('/tmp/agro-panel.lock', 'w')
try:
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("El panel ya esta corriendo en otra instancia.")
    sys.exit(1)

import curses
import threading
import time
import sys
import os
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import DISPOSITIVOS, PUERTO_SERIE, BAUDRATE
import firebase_client as fb
import serial_client as serie

estado = {
    "sensor": {"temperatura": "-", "humedad": "-", "timestamp": "-"},
    "bmp180": {"presion": "-", "temperatura": "-", "altitud": "-", "timestamp": "-"},
    "firebase": {"ok": False, "ultimo_arranque": "-", "version": "-"},
    "usb": {"conectado": False, "puerto": "-"},
    "web": {"ip": "-", "modo": "-", "red": "-", "nombre": "-"},
    "bot": {"activo_local": False, "instalado": False, "habilitado": False,
            "corriendo_remoto": False, "equipo_remoto": "-"},
    "monitor": [],
    "corriendo": True
}

MAX_LINEAS_MONITOR = 20

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
                estado["web"]["ip"]     = est.get("ip", "-")
                estado["web"]["modo"]   = est.get("modo", "-")
                estado["web"]["red"]    = est.get("red", "-")
                estado["web"]["nombre"] = est.get("nombre", "-")
                estado["firebase"]["ultimo_arranque"] = est.get("ultimo_arranque", "-")
                estado["firebase"]["version"]         = est.get("version", "-")

            lectura_bmp = fb.leer("/sensores/bmp180/ultima_lectura")
            if lectura_bmp:
                estado["bmp180"]["presion"]     = str(lectura_bmp.get("presion", "-"))
                estado["bmp180"]["temperatura"] = str(lectura_bmp.get("temperatura", "-"))
                estado["bmp180"]["altitud"]     = str(lectura_bmp.get("altitud", "-"))
                estado["bmp180"]["timestamp"]   = lectura_bmp.get("timestamp", "-")

        except:
            estado["firebase"]["ok"] = False
        time.sleep(30)

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

def hilo_bot():
    while estado["corriendo"]:
        try:
            r1 = subprocess.run(["systemctl", "is-active", "agro-bot"],
                                capture_output=True, text=True)
            r2 = subprocess.run(["systemctl", "is-enabled", "agro-bot"],
                                capture_output=True, text=True)
            estado["bot"]["activo_local"] = r1.stdout.strip() == "active"
            estado["bot"]["instalado"]    = r2.stdout.strip() in ("enabled", "disabled")
            estado["bot"]["habilitado"]   = r2.stdout.strip() == "enabled"
        except:
            pass
        try:
            datos = fb.leer("/bots/agropanel_bot")
            estado["bot"]["corriendo_remoto"] = datos.get("corriendo", False) if datos else False
            estado["bot"]["equipo_remoto"]    = datos.get("equipo", "-") if datos else "-"
        except:
            pass
        time.sleep(15)

def estado_servicio_bot():
    # Estado local del servicio
    try:
        r1 = subprocess.run(["systemctl", "is-active", "agro-bot"],
                            capture_output=True, text=True)
        r2 = subprocess.run(["systemctl", "is-enabled", "agro-bot"],
                            capture_output=True, text=True)
        activo_local   = r1.stdout.strip() == "active"
        instalado      = r2.stdout.strip() in ("enabled", "disabled")
        habilitado     = r2.stdout.strip() == "enabled"
    except:
        activo_local, instalado, habilitado = False, False, False

    # Estado remoto desde Firebase
    try:
        datos = fb.leer("/bots/agropanel_bot")
        corriendo_remoto = datos.get("corriendo", False) if datos else False
        equipo_remoto    = datos.get("equipo", "-") if datos else "-"
    except:
        corriendo_remoto = False
        equipo_remoto    = "-"

    return activo_local, instalado, habilitado, corriendo_remoto, equipo_remoto

def dibujar_recuadro(win, y, x, h, w, titulo=""):
    win.attron(curses.color_pair(3))
    win.addstr(y, x, "╔" + "═" * (w-2) + "╗")
    for i in range(1, h-1):
        win.addstr(y+i, x, "║")
        win.addstr(y+i, x+w-1, "║")
    win.addstr(y+h-1, x, "╚" + "═" * (w-2) + "╝")
    if titulo:
        win.attron(curses.color_pair(4))
        win.addstr(y, x+2, f" {titulo} ")
    win.attroff(curses.color_pair(4))
    win.attroff(curses.color_pair(3))

def dibujar_panel(win):
    win.erase()
    alto, ancho = win.getmaxyx()

    curses.init_pair(1, curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED,    curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN,   curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_WHITE,  curses.COLOR_BLACK)

    titulo = "Agro - Panel de Control"
    win.attron(curses.color_pair(4) | curses.A_BOLD)
    win.addstr(0, (ancho - len(titulo)) // 2, titulo)
    win.attroff(curses.color_pair(4) | curses.A_BOLD)

    ancho_cuad = ancho // 4
    alto_cuad  = 7

    # Cuadrante 1: Sensor
    nombre_disp = estado["web"]["nombre"]
    titulo_sensor = nombre_disp if nombre_disp != "-" else "Sensor DHT11"
    dibujar_recuadro(win, 2, 0, alto_cuad, ancho_cuad, titulo_sensor)
    win.attron(curses.color_pair(5))
    win.addstr(4, 2, f"Temp : {estado['sensor']['temperatura']} C")
    win.addstr(5, 2, f"Hum  : {estado['sensor']['humedad']} %")
    ts = estado['sensor']['timestamp']
    win.addstr(6, 2, f"Hora : {ts[11:] if len(ts) > 11 else ts}")
    win.attroff(curses.color_pair(5))

    # Cuadrante 2: USB
    dibujar_recuadro(win, 2, ancho_cuad, alto_cuad, ancho_cuad, "Conexion USB")
    if estado["usb"]["conectado"]:
        win.attron(curses.color_pair(1))
        win.addstr(4, ancho_cuad+2, "● Conectado")
        win.attroff(curses.color_pair(1))
        win.attron(curses.color_pair(5))
        win.addstr(5, ancho_cuad+2, estado["usb"]["puerto"][:ancho_cuad-4])
        win.attroff(curses.color_pair(5))
    else:
        win.attron(curses.color_pair(2))
        win.addstr(4, ancho_cuad+2, "● Sin conexion")
        win.attroff(curses.color_pair(2))

    # Cuadrante 3: Web
    dibujar_recuadro(win, 2, ancho_cuad*2, alto_cuad, ancho_cuad, "Conexion Web")
    if estado["web"]["ip"] != "-":
        nombre = estado['web']['nombre']
        if nombre == "-":
            nombre = "En red"
        win.attron(curses.color_pair(1))
        win.addstr(4, ancho_cuad*2+2, f"● {nombre[:ancho_cuad-6]}")
        win.attroff(curses.color_pair(1))
        win.attron(curses.color_pair(5))
        win.addstr(5, ancho_cuad*2+2, f"IP  : {estado['web']['ip'][:ancho_cuad-8]}")
        win.addstr(6, ancho_cuad*2+2, f"Modo: {estado['web']['modo'][:ancho_cuad-8]}")
        win.attroff(curses.color_pair(5))
    else:
        win.attron(curses.color_pair(2))
        win.addstr(4, ancho_cuad*2+2, "● Sin datos")
        win.attroff(curses.color_pair(2))

    # Cuadrante 4: Firebase
    dibujar_recuadro(win, 2, ancho_cuad*3, alto_cuad, ancho - ancho_cuad*3, "Firebase")
    if estado["firebase"]["ok"]:
        win.attron(curses.color_pair(1))
        win.addstr(4, ancho_cuad*3+2, "● Conectado")
        win.attroff(curses.color_pair(1))
        win.attron(curses.color_pair(5))
        win.addstr(5, ancho_cuad*3+2, f"v{estado['firebase']['version']}")
        arr = estado['firebase']['ultimo_arranque']
        win.addstr(6, ancho_cuad*3+2, arr[11:] if len(arr) > 11 else arr)
        win.attroff(curses.color_pair(5))
    else:
        win.attron(curses.color_pair(2))
        win.addstr(4, ancho_cuad*3+2, "● Sin datos")
        win.attroff(curses.color_pair(2))

# Fila 2: Bot y BMP180
    alto_fila2 = 6
    dibujar_recuadro(win, alto_cuad+2, 0, alto_fila2, ancho_cuad*2, "Bot Telegram")
    activo    = estado["bot"]["activo_local"]
    instalado = estado["bot"]["instalado"]
    habilitado = estado["bot"]["habilitado"]
    corriendo_remoto = estado["bot"]["corriendo_remoto"]
    equipo_remoto    = estado["bot"]["equipo_remoto"]

    if not instalado:
        if corriendo_remoto:
            win.attron(curses.color_pair(4))
            win.addstr(alto_cuad+4, 2, f"● Corriendo en: {equipo_remoto[:ancho_cuad*2-20]}")
            win.attroff(curses.color_pair(4))
        else:
            win.attron(curses.color_pair(2))
            win.addstr(alto_cuad+4, 2, "● No instalado localmente")
            win.attroff(curses.color_pair(2))
    else:
        if activo:
            win.attron(curses.color_pair(1))
            win.addstr(alto_cuad+4, 2, "● Corriendo (local)")
            win.attroff(curses.color_pair(1))
        elif corriendo_remoto:
            win.attron(curses.color_pair(4))
            win.addstr(alto_cuad+4, 2, f"● Corriendo en: {equipo_remoto[:ancho_cuad*2-20]}")
            win.attroff(curses.color_pair(4))
        else:
            win.attron(curses.color_pair(2))
            win.addstr(alto_cuad+4, 2, "● Detenido")
            win.attroff(curses.color_pair(2))
        win.attron(curses.color_pair(5))
        estado_str = "Automatico" if habilitado else "Manual"
        win.addstr(alto_cuad+5, 2, f"Inicio: {estado_str}")
        win.addstr(alto_cuad+6, 2, "[B] Iniciar/Detener  [A] Auto on/off")
        win.attroff(curses.color_pair(5))

    # BMP180
    dibujar_recuadro(win, alto_cuad+2, ancho_cuad*2, alto_fila2, ancho - ancho_cuad*2, "BMP180")
    win.attron(curses.color_pair(5))
    win.addstr(alto_cuad+4, ancho_cuad*2+2, f"Pres : {estado['bmp180']['presion']} hPa")
    win.addstr(alto_cuad+5, ancho_cuad*2+2, f"Temp : {estado['bmp180']['temperatura']} C")
    win.addstr(alto_cuad+6, ancho_cuad*2+2, f"Alt  : {estado['bmp180']['altitud']} m")
    win.attroff(curses.color_pair(5))

    # Monitor Serie
    alto_monitor = alto - alto_cuad - alto_fila2 - 6
    dibujar_recuadro(win, alto_cuad+alto_fila2+2, 0, alto_monitor, ancho, "Monitor Serie en vivo (USB)")
    lineas = estado["monitor"][-(alto_monitor-2):]
    for i, linea in enumerate(lineas):
        try:
            win.attron(curses.color_pair(5))
            win.addstr(alto_cuad+alto_fila2+3+i, 2, linea[:ancho-4])
            win.attroff(curses.color_pair(5))
        except:
            pass

    # Menu inferior
    menu = "[H] Historial  [B] Bot on/off  [A] Auto  [R] Reiniciar  [Q] Salir"
    win.attron(curses.color_pair(4))
    try:
        win.addstr(alto-1, (ancho - len(menu)) // 2, menu)
    except:
        pass
    win.attroff(curses.color_pair(4))
    win.refresh()

def mostrar_historial(win):
    win.nodelay(False)
    win.timeout(-1)
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
    win.nodelay(True)
    win.timeout(500)

def main(win):
    curses.curs_set(0)
    win.nodelay(True)
    win.timeout(500)
    t_fb = threading.Thread(target=hilo_firebase, daemon=True)
    t_se = threading.Thread(target=hilo_serie,    daemon=True)
    t_bt = threading.Thread(target=hilo_bot,      daemon=True)
    t_fb.start()
    t_se.start()
    t_bt.start()

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
            elif tecla in (ord('b'), ord('B')):
                if estado["bot"]["instalado"]:
                    if estado["bot"]["activo_local"]:
                        subprocess.run(["sudo", "systemctl", "stop", "agro-bot"],
                                       capture_output=True)
                        estado["monitor"].append(">> Bot detenido.")
                    else:
                        subprocess.run(["sudo", "systemctl", "start", "agro-bot"],
                                       capture_output=True)
                        estado["monitor"].append(">> Bot iniciado.")
            elif tecla in (ord('a'), ord('A')):
                if estado["bot"]["instalado"]:
                    if estado["bot"]["habilitado"]:
                        subprocess.run(["sudo", "systemctl", "disable", "agro-bot"],
                                       capture_output=True)
                        estado["monitor"].append(">> Bot: inicio automatico desactivado.")
                    else:
                        subprocess.run(["sudo", "systemctl", "enable", "agro-bot"],
                                       capture_output=True)
                        estado["monitor"].append(">> Bot: inicio automatico activado.")
        except KeyboardInterrupt:
            estado["corriendo"] = False
            break
        except Exception as e:
            pass

if __name__ == "__main__":
    curses.wrapper(main)
