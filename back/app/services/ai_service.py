from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.images import Image
from app.models.violations import Violation
from app.models.alertes import Alerte
from app.schemas.detectRequest import DetectRequest
from app.schemas.alertResponse import AlertResponse


def process_detection(payload: DetectRequest, db: Session):

    # 1. Enregistre l'image
    image = Image(
        url=payload.media_url,
        cloudinary_id=None,
        traite=True,
        notifie=False,
        uploaded_at=datetime.now(timezone.utc)
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    alerts = []

    # 2. Enregistre chaque violation détectée
    for v in payload.violations:
        violation = Violation(
            image_id=image.id,
            classe=v.label,
            confiance=v.confidence,
            detected_at=datetime.now(timezone.utc)
        )
        db.add(violation)
        db.commit()
        db.refresh(violation)

        # 3. Crée l'alerte associée
        alerte = Alerte(
            image_id=image.id,
            type="push",
            statut="unsend",
            envoye_at=datetime.now(timezone.utc)
        )
        db.add(alerte)
        db.commit()
        db.refresh(alerte)

        alerts.append(AlertResponse(
            id=str(alerte.id),
            media_url=payload.media_url,
            violation_label=v.label,
            detected_at=alerte.envoye_at,
            confidence=v.confidence,
            status=alerte.statut
        ))

    return alerts