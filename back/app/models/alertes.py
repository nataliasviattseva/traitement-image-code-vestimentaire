from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models import Base


class Alerte(Base):
    __tablename__ = "alertes"

    id_alerte = Column(Integer, primary_key=True, index=True)

    date_detect = Column(DateTime, default=datetime.utcnow)
    confidence = Column(Float)
    process_status = Column(String)

    id_image = Column(Integer, ForeignKey("images.id_image"))
    id_violation = Column(Integer, ForeignKey("violation.id_violation"))

    image = relationship("Image", back_populates="alertes")
    violation = relationship("Violation", back_populates="alertes")