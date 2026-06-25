# ─────────────────────────────────────────
# firebase_client.py
# Conexion y consultas a Firebase Realtime Database
# ─────────────────────────────────────────

import requests
from config import FIREBASE_DATABASE_URL

TIMEOUT = 10

# ─────────────────────────────────────────
def leer(ruta):
    try:
        url = f"{FIREBASE_DATABASE_URL}{ruta}.json"
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error Firebase leer: {e}")
        return None

# ─────────────────────────────────────────
def escribir(ruta, valor):
    try:
        url = f"{FIREBASE_DATABASE_URL}{ruta}.json"
        response = requests.put(url, json=valor, timeout=TIMEOUT)
        return response.status_code == 200
    except Exception as e:
        print(f"Error Firebase escribir: {e}")
        return False

# ─────────────────────────────────────────
def obtener_estado_dispositivo(dispositivo_id):
    return leer(f"/dispositivos/{dispositivo_id}/estado")

# ─────────────────────────────────────────
def obtener_ultima_lectura(ruta_sensores):
    return leer(f"{ruta_sensores}/ultima_lectura")

# ─────────────────────────────────────────
def obtener_historial(ruta_sensores, limite=10):
    data = leer(f"{ruta_sensores}/historial")
    if not data:
        return []
    registros = sorted(data.items(), key=lambda x: x[0], reverse=True)
    return registros[:limite]
