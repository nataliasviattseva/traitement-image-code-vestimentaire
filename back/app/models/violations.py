from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models import Base


class Violation(Base):
    __tablename__ = "violations"

    id_violation = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    description = Column(String)

    alertes = relationship("Alerte", back_populates="violation")