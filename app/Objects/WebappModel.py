from sqlalchemy import Column, String, UUID, func, DateTime

from app.Infrastructure.Database import Base


class Webapp(Base):
    __tablename__ = 'Webapps'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    key = Column(String(255), primary_key=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())