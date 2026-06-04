#!/bin/bash
# ─────────────────────────────────────────
# install.sh
# Instalacion de dependencias para agro-panel
# ─────────────────────────────────────────

echo "Instalando dependencias de agro-panel..."

pip3 install pyserial requests --break-system-packages

echo ""
echo "Configuracion:"
echo "  cp src/config.py.ejemplo src/config.py"
echo "  nano src/config.py"
echo ""
echo "Uso:"
echo "  python3 panel/dashboard.py   # Dashboard visual"
echo "  python3 panel/panel.py       # Panel de texto"
echo ""
echo "Listo!"
