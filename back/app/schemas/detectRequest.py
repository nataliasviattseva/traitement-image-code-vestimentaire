from pydantic import BaseModel
from typing import List


class DetectedViolation(BaseModel):
    label: str
    confidence: float


class DetectRequest(BaseModel):
    media_url: str
    media_type: str
    source: str
    violations: List[DetectedViolation]
