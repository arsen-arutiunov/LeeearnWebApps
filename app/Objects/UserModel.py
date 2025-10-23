from sqlalchemy import (
    Column, UUID, DateTime, func,
    String, BigInteger, Table, ForeignKey
)
from sqlalchemy.orm import relationship

from app.Infrastructure.Database import Base


# Ассоциативная таблица (many-to-many)
user_branch_roles = Table(
    'auth.UserBranchRoles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('auth.Users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('auth.BranchRoles.id', ondelete='CASCADE'), primary_key=True),
    schema='auth'
)


class User(Base):
    __tablename__ = 'Users'
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    branch_id = Column(UUID(as_uuid=True))
    telegram_id = Column(BigInteger, nullable=False, unique=True)

    name = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    roles = relationship(
        "BranchRole",
        secondary=user_branch_roles,
        back_populates="users"
    )
