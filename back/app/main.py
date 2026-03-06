import json
import logging
import os
import uuid
from pathlib import Path
from typing import Set
from dotenv import load_dotenv

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from notification_service import (
    DressCodeAlert,
    EmailConfig,
    NotificationService,
    email_config_from_env,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="ENSITECH — Détection Code Vestimentaire", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # En production : URL exacte du front Flutter/web
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv() 
# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXT = {".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------------------------
# Notification service (singleton)
# ---------------------------------------------------------------------------
# variables d'environnement 
_email_cfg = email_config_from_env()

#  tests locaux :
# _email_cfg = EmailConfig(
#     sender="votre.adresse@gmail.com",
#     password="xxxx xxxx xxxx xxxx",   # App Password Gmail (16 car.)
#     recipients=["responsable@ensitech.fr"],
# )

notifier = NotificationService(email_config=_email_cfg)


# ---------------------------------------------------------------------------
# WebSocket manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket connecté — %d client(s) actif(s)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info("WebSocket déconnecté — %d client(s) actif(s)", len(self.active_connections))

    async def broadcast_json(self, payload: dict) -> None:
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def validate_upload(file: UploadFile) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Type de fichier non supporté (jpg/jpeg/png)")
    if not (file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=400, detail="Content-type invalide (doit être image/*)")
    return ext


async def persist_upload(file: UploadFile, ext: str) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Fichier vide")
    filename = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(data)
    return {
        "filename": filename,
        "content_type": file.content_type,
        "size": len(data),
        "path": str(dest),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "notifications": {
            "email": _email_cfg is not None and _email_cfg.enabled,
            "websocket": True,
        },
    }


@app.post("/media")
async def upload_media(file: UploadFile = File(...)):
    ext = validate_upload(file)
    uploaded = await persist_upload(file, ext)
    return {"ok": True, "uploaded": uploaded}


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Endpoint principal :
    1. Valide et sauvegarde l'image
    2. Appelle le modèle IA (mock à remplacer)
    3. Si non-conforme → broadcast WebSocket + email
    """
    ext = validate_upload(file)
    uploaded = await persist_upload(file, ext)

    # ------------------------------------------------------------------
    # TODO : remplacer ce mock par l'appel réel au service IA
    #   import httpx
    #   async with httpx.AsyncClient() as client:
    #       resp = await client.post("http://ia-service/infer", ...)
    #       ia_result = resp.json()
    # ------------------------------------------------------------------
    ia_result = {
        "ok": True,
        "non_conforme": True,
        "reason": "accessoire_interdit",
        "confidence": 0.92,
        "location": "Entrée bâtiment A",
        "detections": [
            {"label": "casquette", "present": True, "confidence": 0.92},
        ],
    }

    response = {"ok": True, "uploaded": uploaded, "result": ia_result}

    # ------------------------------------------------------------------
    # Notifications si non-conforme
    # ------------------------------------------------------------------
    if ia_result.get("non_conforme"):
        alert = DressCodeAlert(
            filename=uploaded["filename"],
            reason=ia_result.get("reason", "unknown"),
            confidence=ia_result.get("confidence", 0.0),
            location=ia_result.get("location"),
            detections=ia_result.get("detections", []),
        )

        # 1. Broadcast WebSocket (temps réel)
        ws_payload = {
            "type": "DRESS_CODE_ALERT",
            "reason": alert.reason,
            "reason_label": alert.reason_label,
            "confidence": alert.confidence,
            "confidence_pct": alert.confidence_pct,
            "timestamp": alert.timestamp.isoformat(),
            "filename": alert.filename,
            "location": alert.location,
            "detections": alert.detections,
        }
        await manager.broadcast_json(ws_payload)
        logger.info("Alerte WebSocket broadcastée : %s", alert.reason)

        # 2. Email + autres canaux (asynchrone, ne bloque pas la réponse)
        notification_results = await notifier.notify(alert)
        logger.info("Résultats notifications : %s", notification_results)

        response["alert_sent"] = notification_results

    return response


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """
    Endpoint WebSocket pour les clients Flutter / web.
    Le client reçoit un message JSON à chaque détection non-conforme.

    Format du message :
    {
      "type": "DRESS_CODE_ALERT",
      "reason": "accessoire_interdit",
      "reason_label": "Accessoire interdit (casquette, bonnet…)",
      "confidence": 0.92,
      "confidence_pct": "92.0%",
      "timestamp": "2026-03-06T10:30:00",
      "filename": "uuid.jpg",
      "location": "Entrée bâtiment A",
      "detections": [...]
    }
    """
    await manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "INFO",
            "message": "Connecté au système d'alertes ENSITECH",
        }))
        while True:
            # Maintien de la connexion — le client peut envoyer des pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)