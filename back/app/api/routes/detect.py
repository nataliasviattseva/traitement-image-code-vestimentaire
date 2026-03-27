from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.images import Image
from app.models.violations import Violation
from app.models.alertes import Alerte
from app.api.websocket.alerts_ws import manager

router = APIRouter()

@router.post("/ia/report")
async def ia_report(payload: dict, db: Session = Depends(get_db)):
    image_url = payload.get("image_url")
    violation_label = payload.get("violation")
    score = payload.get("score")

    # 1. Save the image
    image = Image(
        url_cloudinary=image_url,
        type_media="image",
        processed=True
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    # 2. Get or create the violation
    violation = db.query(Violation).filter_by(label=violation_label).first()
    if not violation:
        violation = Violation(label=violation_label)
        db.add(violation)
        db.commit()
        db.refresh(violation)

    # 3. Create the alert
    alerte = Alerte(
        id_media=image.id_media,
        id_violation=violation.id_violation
    )
    db.add(alerte)
    db.commit()
    db.refresh(alerte)

    # 4. Notify via WebSocket
    await manager.broadcast(f"Alerte : {violation.label} détectée")

    return {
        "status": "ok",
        "alerte_id": alerte.id_alerte
    }

