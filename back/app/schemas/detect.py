from pydantic import BaseModel
from typing import Optional


class DetectionRequest(BaseModel):
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class DetectionResult(BaseModel):
    violation_type: str
    confidence: float