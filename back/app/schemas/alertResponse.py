from pydantic import BaseModel
from datetime import datetime

class AlertResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str                # UUID → str
    media_url: str
    violation_label: str
    detected_at: datetime
    confidence: float
    status: str