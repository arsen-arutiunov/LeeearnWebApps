from sqlalchemy import UUID, Column, String, func, DateTime

from app.Infrastructure.Database import Base


class BranchRole(Base):
    __tablename__ = 'BranchRoles'

    id = Column(UUID(as_uuid=True), primary_key=True)
    branch_id = Column(UUID(as_uuid=True), nullable=False)

    name = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())