from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base

class Violation(Base):
    __tablename__ = "violations"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id    = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=False)
    classe      = Column(String, nullable=False)   # ex: "casquette"
    confiance   = Column(Float, nullable=False)
    bbox_x      = Column(Float, nullable=True)
    bbox_y      = Column(Float, nullable=True)
    bbox_w      = Column(Float, nullable=True)
    bbox_h      = Column(Float, nullable=True)
    detected_at = Column(DateTime, nullable=True)

    image       = relationship("Image", back_populates="violations")
