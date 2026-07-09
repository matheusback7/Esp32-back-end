"""
Backend para ESP32 DevKit1: autenticação + dashboard de monitoramento em tempo real.

Rotas principais:
- POST /api/login              -> login do usuário do dashboard, retorna JWT
- GET  /api/devices             -> lista dispositivos e últimas leituras (protegida por JWT)
- POST /api/devices/{id}/command-> envia comando para um ESP32 (protegida por JWT)
- WS   /ws/device?api_key=...&device_id=...  -> ESP32 conecta e envia leituras
- WS   /ws/dashboard?token=...                -> dashboard conecta e recebe tudo em tempo real
- GET  /                        -> serve o dashboard estático
"""
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.auth import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_current_user,
    verify_device_api_key,
)
from app.config import settings
from app.websocket_manager import manager

app = FastAPI(title="ESP32 DevKit1 Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class LoginRequest(BaseModel):
    username: str
    password: str


class CommandRequest(BaseModel):
    command: str
    payload: dict | None = None


@app.get("/")
def dashboard_page():
    return FileResponse("static/dashboard.html")


@app.post("/api/login")
def login(req: LoginRequest):
    if not authenticate_user(req.username, req.password):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    token = create_access_token(req.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/devices")
def list_devices(user: str = Depends(get_current_user)):
    return {"devices": manager.latest_readings}


@app.post("/api/devices/{device_id}/command")
async def send_command(device_id: str, req: CommandRequest, user: str = Depends(get_current_user)):
    ok = await manager.send_command_to_device(
        device_id, {"command": req.command, "payload": req.payload or {}}
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Dispositivo não conectado")
    return {"status": "enviado"}


# ---------------- WebSocket: ESP32 ----------------
@app.websocket("/ws/device")
async def ws_device(websocket: WebSocket, device_id: str = Query(...), api_key: str = Query(...)):
    if not verify_device_api_key(api_key):
        await websocket.close(code=4401)
        return

    await manager.connect_device(device_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            await manager.register_reading(device_id, data)
    except WebSocketDisconnect:
        manager.disconnect_device(device_id)
        await manager.broadcast_to_dashboard(
            {"type": "device_status", "device_id": device_id, "status": "offline"}
        )


# ---------------- WebSocket: Dashboard ----------------
@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket, token: str = Query(...)):
    try:
        decode_access_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    await manager.connect_dashboard(websocket)
    try:
        while True:
            # Mantém a conexão viva; dashboard não precisa enviar nada
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket)
