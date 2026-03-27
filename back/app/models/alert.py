from sqlalchemy import Column, ForeignKey, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base

class Alert(Base):
    __tablename__ = "alert"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=False)
    violation_id = Column(UUID(as_uuid=True), ForeignKey("violation.id"), nullable=False)

    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    confidence = Column(Float, nullable=False)
    status = Column(String)
    sent_email = Column(Boolean, default=False)
    sent_mobile = Column(Boolean, default=False)

