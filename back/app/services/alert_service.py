import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.media import Media
from app.models.violation import Violation
from app.models.alert import Alert
from app.schemas.detect import DetectRequest
from app.schemas.alert import AlertResponse
from datetime import datetime, timezone

# Service to process detection results and create alerts in the database
def process_detection(payload: DetectRequest, db: Session):
    media_id = str(uuid.uuid4())

    # Create alert in DB
    media = Media(
        id=media_id,
        url=payload.media_url,
        type=payload.media_type,
        source=payload.source,
    )
    db.add(media)
    db.commit()

    alerts = []

    # For each detected violation, create an alert
    for v in payload.violations:
        violation = db.query(Violation).filter(Violation.label == v.label).first()
        if not violation:
            continue  # ou raise

        # Create alert
        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            media_id=media_id,
            violation_id=violation.id,
            confidence=v.confidence,
        )
        db.add(alert)
        db.commit()

        # Prepare response for WebSocket broadcast
        alerts.append(AlertResponse(
            id=alert_id,
            media_url=payload.media_url,
            violation_label=violation.label,
            violation_category=violation.category,
            detected_at=datetime,
            confidence=v.confidence,
            status="new",
        ))

    return alerts