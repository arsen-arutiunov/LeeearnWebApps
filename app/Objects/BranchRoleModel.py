from sqlalchemy import UUID, Column, String, func, DateTime
from sqlalchemy.orm import relationship

from app.Infrastructure.Database import Base
from app.Objects.UserModel import user_branch_roles


class BranchRole(Base):
    __tablename__ = 'BranchRoles'
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    branch_id = Column(UUID(as_uuid=True), nullable=False)

    name = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship(
        "User",
        secondary=user_branch_roles,
        back_populates="roles"
    )