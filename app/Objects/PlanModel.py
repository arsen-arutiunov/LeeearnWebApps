import uuid
from sqlalchemy import Column, String, Integer, Numeric, UUID, text, ForeignKey, func, DateTime
from app.Infrastructure.Database import Base

class Plan(Base):
    __tablename__ = "Plans"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    webapp_id = Column(UUID(as_uuid=True), ForeignKey("Webapps.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())