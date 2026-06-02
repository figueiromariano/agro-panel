#!/usr/bin/env python3
# ─────────────────────────────────────────
# panel.py
# Panel de control principal del proyecto Agro
# ─────────────────────────────────────────

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import DISPOSITIVOS
import firebase_client as fb
import serial_client as serie

# ─────────────────────────────────────────
def limpiar():
    os.system('clear')

# ─────────────────────────────────────────
def encabezado():
    print("═" * 50)
    print("       Agro - Panel de Control")
    print("═" * 50)

# ─────────────────────────────────────────
def menu_principal():
    limpiar()
    encabezado()
    print()
    print("  [1] Estado del dispositivo")
    print("  [2] Ultima lectura del sensor")
    print("  [3] Historial de lecturas")
    print("  [4] Monitor serie en vivo (USB)")
    print("  [5] Reiniciar ESP32 (USB)")
    print("  [6] Salir")
    print()
    print("─" * 50)
    return input("  Opcion: ").strip()

# ─────────────────────────────────────────
def mostrar_estado():
    limpiar()
    encabezado()
    print("\n  Estado del dispositivo\n")
    print("  Consultando Firebase...")

    dispositivo = DISPOSITIVOS["dht11_esp32"]
    estado = fb.obtener_estado_dispositivo("dht11_esp32")

    if not estado:
        print("  No se pudo obtener el estado.")
    else:
        print(f"\n  Dispositivo : {dispositivo['nombre']}")
        print(f"  Modo        : {estado.get('modo', '-')}")
        print(f"  Red WiFi    : {estado.get('red', '-')}")
        print(f"  IP          : {estado.get('ip', '-')}")
        print(f"  Arranque    : {estado.get('ultimo_arranque', '-')}")
        print(f"  Version     : {estado.get('version', '-')}")

        ip = estado.get('ip')
        if ip:
            print(f"\n  Interfaz web: http://{ip}")

    print()
    input("  Enter para volver...")

# ─────────────────────────────────────────
def mostrar_ultima_lectura():
    limpiar()
    encabezado()
    print("\n  Ultima lectura del sensor\n")
    print("  Consultando Firebase...")

    dispositivo = DISPOSITIVOS["dht11_esp32"]
    lectura = fb.obtener_ultima_lectura(dispositivo["ruta_sensores"])

    if not lectura:
        print("  No se encontraron datos.")
    else:
        print(f"\n  Temperatura : {lectura.get('temperatura', '-')} {lectura.get('unidad_temp', '')}")
        print(f"  Humedad     : {lectura.get('humedad', '-')} %")
        print(f"  Timestamp   : {lectura.get('timestamp', '-')}")

    print()
    input("  Enter para volver...")

# ─────────────────────────────────────────
def mostrar_historial():
    limpiar()
    encabezado()
    print("\n  Historial de lecturas (ultimas 10)\n")
    print("  Consultando Firebase...")

    dispositivo = DISPOSITIVOS["dht11_esp32"]
    historial = fb.obtener_historial(dispositivo["ruta_sensores"], 10)

    if not historial:
        print("  No se encontraron registros.")
    else:
        print()
        print(f"  {'Timestamp':<25} {'Temp':>6} {'Humedad':>8}")
        print("  " + "─" * 42)
        for clave, datos in historial:
            fecha, hora = clave.split("_")
            hora = hora.replace("-", ":")
            ts = f"{fecha} {hora}"
            tmp = datos.get('temperatura', '-')
            hum = datos.get('humedad', '-')
            print(f"  {ts:<25} {str(tmp)+' C':>6} {str(hum)+' %':>8}")

    print()
    input("  Enter para volver...")

# ─────────────────────────────────────────
def monitor_serie():
    limpiar()
    encabezado()
    print("\n  Monitor serie en vivo\n")
    puertos = serie.listar_puertos()
    if not puertos:
        print("  No se encontraron puertos serie.")
        input("  Enter para volver...")
        return
    if len(puertos) == 1:
        puerto = puertos[0]
        print(f"  Conectando a {puerto}...")
    else:
        print("  Puertos disponibles:")
        for i, p in enumerate(puertos):
            print(f"    [{i+1}] {p}")
        print()
        idx = input("  Selecciona puerto: ").strip()
        puerto = puertos[int(idx)-1] if idx.isdigit() else puertos[0]
    serie.conectar(puerto)
    serie.monitor_en_vivo(duracion=120)
    serie.desconectar()
    input("  Enter para volver...")

# ─────────────────────────────────────────
def reiniciar_dispositivo():
    limpiar()
    encabezado()
    print("\n  Reiniciar ESP32\n")
    confirmar = input("  Confirmas el reinicio? (s/n): ").strip().lower()
    if confirmar == 's':
        serie.conectar()
        serie.reiniciar_esp32()
        serie.desconectar()
    else:
        print("  Cancelado.")
    input("  Enter para volver...")

# ─────────────────────────────────────────
def main():
    while True:
        opcion = menu_principal()
        if opcion == '1':
            mostrar_estado()
        elif opcion == '2':
            mostrar_ultima_lectura()
        elif opcion == '3':
            mostrar_historial()
        elif opcion == '4':
            monitor_serie()
        elif opcion == '5':
            reiniciar_dispositivo()
        elif opcion == '6':
            print("\n  Hasta luego!\n")
            break
        else:
            print("  Opcion invalida.")
            time.sleep(1)

if __name__ == "__main__":
    main()
