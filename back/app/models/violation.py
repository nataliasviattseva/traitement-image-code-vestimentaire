from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Violation(Base):
    __tablename__ = "violation"

    id_violation = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    description = Column(String)

    alerts = relationship("Alert", back_populates="violation")