from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import uuid
from app.models.base import Base

class Alerte(Base):
    __tablename__ = "alertes"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id  = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=False)
    type      = Column(String, nullable=True)
    statut    = Column(String, nullable=True)
    envoye_at = Column(DateTime, nullable=True)

    image     = relationship("Image", back_populates="alertes")

