from fastapi import APIRouter
from app.schemas.detect import DetectionRequest, DetectionResult

router = APIRouter()


@router.post("/detect", response_model=DetectionResult)
async def detect_violation(data: DetectionRequest):

    # appel IA ici
    result = {
        "violation_type": "no_helmet",
        "confidence": 0.92
    }

    return result