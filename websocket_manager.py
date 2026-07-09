"""
Gerencia conexões WebSocket e o estado em tempo real (em memória, sem banco).

- Dispositivos ESP32 conectam em /ws/device e enviam leituras.
- Clientes do dashboard conectam em /ws/dashboard e recebem tudo em tempo real.
"""
import json
from datetime import datetime, timezone

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.dashboard_clients: list[WebSocket] = []
        self.devices: dict[str, WebSocket] = {}
        # Último estado conhecido de cada dispositivo (somente em memória)
        self.latest_readings: dict[str, dict] = {}

    # ---- Dashboard ----
    async def connect_dashboard(self, ws: WebSocket):
        await ws.accept()
        self.dashboard_clients.append(ws)
        # Ao conectar, manda o snapshot atual
        await ws.send_json({"type": "snapshot", "devices": self.latest_readings})

    def disconnect_dashboard(self, ws: WebSocket):
        if ws in self.dashboard_clients:
            self.dashboard_clients.remove(ws)

    # ---- Dispositivos ----
    async def connect_device(self, device_id: str, ws: WebSocket):
        await ws.accept()
        self.devices[device_id] = ws
        await self.broadcast_to_dashboard(
            {"type": "device_status", "device_id": device_id, "status": "online"}
        )

    def disconnect_device(self, device_id: str):
        self.devices.pop(device_id, None)

    async def register_reading(self, device_id: str, data: dict):
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.latest_readings[device_id] = data
        await self.broadcast_to_dashboard(
            {"type": "reading", "device_id": device_id, "data": data}
        )

    async def broadcast_to_dashboard(self, message: dict):
        dead = []
        for client in self.dashboard_clients:
            try:
                await client.send_json(message)
            except Exception:
                dead.append(client)
        for d in dead:
            self.disconnect_dashboard(d)

    async def send_command_to_device(self, device_id: str, command: dict) -> bool:
        ws = self.devices.get(device_id)
        if not ws:
            return False
        await ws.send_text(json.dumps(command))
        return True


manager = ConnectionManager()
