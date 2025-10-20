import enum

from sqlalchemy import Column, UUID, ForeignKey, func, DateTime, Boolean, UniqueConstraint
from sqlalchemy.dialects.mysql import ENUM

from app.Infrastructure.Database import Base


class SubscriptionStatus(enum.Enum):
    expired = 0
    active = 1
    cancelled = 2

class Subscription(Base):
    __tablename__ = 'Subscriptions'

    __table_args__ = (
        UniqueConstraint("branch_id", "webapp_id", name="uq_branch_webapp_subscription"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    branch_id = Column(UUID(as_uuid=True), ForeignKey('Branches.id'), nullable=False)
    webapp_id = Column(UUID(as_uuid=True), ForeignKey('Webapps.id'), nullable=False)

    status = Column(ENUM(SubscriptionStatus), default=SubscriptionStatus.active, nullable=False)

    plan_id = Column(UUID(as_uuid=True), ForeignKey("Plans.id"), nullable=False)
    active_until = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())