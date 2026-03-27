from pydantic import BaseModel
from typing import Optional
from app.utils.database import SessionLocal
from app.services.alert_service import create_alert
from fastapi import UploadFile, File
from app.main import app, manager
from app.utils.file_utils import validate_upload, persist_upload



class DetectionRequest(BaseModel):
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class DetectionResult(BaseModel):
    violation_type: str
    confidence: float

# Note: This is a mock implementation. In a real scenario, you would call your IA model here.
@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    ext = validate_upload(file)
    uploaded = await persist_upload(file, ext)

    # MOCK IA
    ia_result = {
        "ok": True,
        "non_conforme": True,
        "reason": "no_helmet",
        "confidence": 0.92,
        "detections": [{"label": "helmet", "present": False, "confidence": 0.92}],
    }

    response = {"ok": True, "uploaded": uploaded, "result": ia_result}

    if ia_result.get("non_conforme") is True:

        db = SessionLocal()

        alert = create_alert(
            db=db,
            media_path=uploaded["path"],
            violation_label=ia_result.get("reason"),
            confidence=ia_result.get("confidence"),
        )

        db.close()

        alert_payload = {
            "type": "ALERT",
            "reason": ia_result.get("reason"),
            "confidence": ia_result.get("confidence"),
            "filename": uploaded["filename"],
        }

        await manager.broadcast_json(alert_payload)

    return response