from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertBase(BaseModel):
    violation_type: str
    confidence: float
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    location: Optional[str] = None


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True