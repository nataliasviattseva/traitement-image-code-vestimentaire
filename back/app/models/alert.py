from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Alert(Base):
    __tablename__ = "alert"

    id_alert = Column(Integer, primary_key=True, index=True)

    date_detect = Column(DateTime, default=datetime.utcnow)
    confidence = Column(Float)
    process_status = Column(String)

    id_media = Column(Integer, ForeignKey("media.id_media"))
    id_violation = Column(Integer, ForeignKey("violation.id_violation"))

    media = relationship("Media", back_populates="alerts")
    violation = relationship("Violation", back_populates="alerts")