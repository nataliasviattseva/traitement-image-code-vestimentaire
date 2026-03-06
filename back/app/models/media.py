from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Media(Base):
    __tablename__ = "media"

    id_media = Column(Integer, primary_key=True, index=True)
    url_cloudinary = Column(String, nullable=False)
    type_media = Column(String)  # image ou video
    date_upload = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    alerts = relationship("Alert", back_populates="media")