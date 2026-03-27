from pydantic import BaseModel

class IAReport(BaseModel):
    image_url: str
    violation: str
    score: float
