# ─────────────────────────────────────────
# firebase_client.py
# Conexión y consultas a Firebase Realtime Database
# ─────────────────────────────────────────

import requests
import json
from config import FIREBASE_DATABASE_URL, FIREBASE_API_KEY

# ─────────────────────────────────────────
def obtener_token():
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    response = requests.post(url, json={"returnSecureToken": True})
    if response.status_code == 200:
        return response.json().get("idToken")
    return None

# ─────────────────────────────────────────
def leer(ruta):
    token = obtener_token()
    if not token:
        return None
    url = f"{FIREBASE_DATABASE_URL}{ruta}.json?auth={token}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

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
    # Ordenar por timestamp y tomar los últimos N
    registros = sorted(data.items(), key=lambda x: x[0], reverse=True)
    return registros[:limite]
