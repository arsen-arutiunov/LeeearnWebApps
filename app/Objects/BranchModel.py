from sqlalchemy import UUID, Column, String, func, DateTime

from app.Infrastructure.Database import Base


class Branch(Base):
    __tablename__ = 'Branches'

    id = Column(UUID(as_uuid=True), primary_key=True)

    title = Column(String(255), nullable=False)
    icon = Column(String(255), nullable=True)
    color = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())