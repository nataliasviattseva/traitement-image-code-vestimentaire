from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.detectRequest import DetectRequest
from app.services.ai_service import process_detection
from app.services.alert_service import manager
from app.utils.database import get_db

router = APIRouter()

@router.post("/ia/report")
async def ia_report(payload: DetectRequest, db: Session = Depends(get_db)):
    alerts = process_detection(payload, db)

    for alert in alerts:
        await manager.broadcast_json(alert.model_dump(mode="json"))

    return {"status": "ok", "count": len(alerts)}
