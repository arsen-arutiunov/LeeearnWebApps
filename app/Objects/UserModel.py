from sqlalchemy import Column, UUID, DateTime, func, String
from sqlalchemy.dialects.postgresql import ARRAY

from app.Infrastructure.Database import Base


class User(Base):
    __tablename__ = 'Users'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    branch_id = Column(UUID(as_uuid=True))

    name = Column(String(255), nullable=False)
    roles = Column(ARRAY(UUID(as_uuid=True)), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())