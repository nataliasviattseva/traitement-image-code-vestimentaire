from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models import Base


class Image(Base):
    __tablename__ = "images"

    id_image = Column(Integer, primary_key=True, index=True)
    url_cloudinary = Column(String, nullable=False)
    type_image = Column(String)  # image ou video
    date_upload = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    alertes = relationship("Alerte", back_populates="image")