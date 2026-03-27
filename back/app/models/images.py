from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base

class Image(Base):
    __tablename__ = "images"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url           = Column(String, nullable=False)
    cloudinary_id = Column(String, nullable=True)
    traite        = Column(Boolean, default=False)
    notifie       = Column(Boolean, default=False)
    uploaded_at   = Column(DateTime, nullable=True)
    traite_at     = Column(DateTime, nullable=True)

    alertes    = relationship("Alerte", back_populates="image")
    violations = relationship("Violation", back_populates="image")