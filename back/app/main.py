from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Set
import json

from app.utils.database import engine
from app.models import Base
from app.utils.database import SessionLocal
from app.models import alertes

# Import des routes
from app.api.routes.detect import router as detect_router

from app.models import images, violations

# --- FastAPI app ---
app = FastAPI(title="Projet IA", version="0.1.0")

# Création des tables
#Base.metadata.create_all(bind=engine)
app = FastAPI(title="Projet IA", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_json(self, payload: dict):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

manager = ConnectionManager()

# --- Routes ---
app.include_router(detect_router, prefix="/api")

# --- WebSocket ---
@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({"type": "INFO", "message": "connected"}))
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
