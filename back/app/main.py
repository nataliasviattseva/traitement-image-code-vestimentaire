from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.database import engine, Base
from app.models import media, alert, violation
from app.database import SessionLocal
from app.models.violation import Violation
import uuid
import json
import os
import httpx

from typing import Set


app = FastAPI(title="Projet IA", version="0.1.0")
Base.metadata.create_all(bind=engine)

# CORS (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: mettre l'url exacte du front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload settings
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png"}


# --- WebSocket manager (simple) ---
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


def validate_upload(file: UploadFile) -> str:
    """
    Validate an uploaded image; returns ext if ok.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type (jpg/jpeg/png only)")

    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid content-type (must be image/*)")

    return ext


async def persist_upload(file: UploadFile, ext: str) -> dict:
    """
    Read file bytes, persist to disk, and return metadata.
    """
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    filename = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(data)

    return {
        "filename": filename,
        "content_type": file.content_type,
        "size": len(data),
        "path": str(dest),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/media")
async def upload_media(file: UploadFile = File(...)):
    ext = validate_upload(file)
    uploaded = await persist_upload(file, ext)
    return {"ok": True, "uploaded": uploaded}


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    ext = validate_upload(file)
    uploaded = await persist_upload(file, ext)

    # MOCK IA (à remplacer par appel HTTP vers service IA)
    ia_result = {
        "ok": True,
        "non_conforme": True,
        "reason": "no_helmet",
        "confidence": 0.92,
        "detections": [{"label": "helmet", "present": False, "confidence": 0.92}],
    }

    response = {"ok": True, "uploaded": uploaded, "result": ia_result}

    # Si non-conforme -> broadcast WS
    if ia_result.get("non_conforme") is True:
        alert_payload = {
            "type": "ALERT",
            "reason": ia_result.get("reason"),
            "confidence": ia_result.get("confidence"),
            "filename": uploaded["filename"],
        }
        await manager.broadcast_json(alert_payload)

    return response


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # petit message de bienvenue (utile pour debug)
        await websocket.send_text(json.dumps({"type": "INFO", "message": "connected"}))

        while True:
            # On garde la connexion vivante. Si le client envoie des pings, on les lit.
            _ = await websocket.receive_text()
            # Optionnel: répondre au ping
            # await websocket.send_text(json.dumps({"type": "PONG"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)



@app.get("/test-db")
def test_db():
    db = SessionLocal()

    violation = Violation(
        label="casquette",
        description="Port de casquette interdit"
    )

    db.add(violation)
    db.commit()

    return {"message": "violation créée"}
