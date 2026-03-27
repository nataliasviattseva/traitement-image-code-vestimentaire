from fastapi import APIRouter
from back.app.schemas.detectRequest import DetectionRequest, DetectionResult
from app.utils.file_utils import extract_public_id



router = APIRouter()


@router.post("/detect", response_model=DetectionResult)
async def detect_violation(data: DetectionRequest):

    # get media URL from request (could be image or video)
    media_url = data.image_url

    # extract public_id Cloudinary (TTL/purge preparation)
    public_id = extract_public_id(media_url)

    # appel IA ici
    result = {
        "violation_type": "no_helmet",
        "confidence": 0.92
    }

    return result