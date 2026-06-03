
## Notebook dedicada
- Configurar el bot, panel y agente en una notebook de bajo consumo
- Dejar todo iniciando automaticamente al encender

## Panel - nuevo recuadro
- Agregar recuadro en el dashboard que muestre si el bot esta corriendo
- Opcion para iniciarlo desde el panel si no esta activo

## Bot - control de instancias
- Un bot de Telegram no puede correr en dos lugares a la vez
  (Telegram rechaza el segundo polling automaticamente)
- Aprovechar esto para detectar si ya hay un bot corriendo
- Publicar en Firebase el estado del bot:
    bots/agropanel_bot/estado/
      corriendo: true/false
      equipo: "nombre del equipo"
      inicio: "2026-06-03 19:30:00"
- El panel consulta Firebase para saber si hay bot activo
- Si no hay bot activo, ofrecer iniciarlo manual o automaticamente
- Agregar comando /estado al bot que informe desde que equipo esta corriendo
