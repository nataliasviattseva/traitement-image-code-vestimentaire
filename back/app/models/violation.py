from sqlalchemy import Column, String
from  app.models.base import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Violation(Base):
    __tablename__ = "violation"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String, nullable=False)
    category = Column(String, nullable=False) # bas | haut | chaussures | accessoire

 