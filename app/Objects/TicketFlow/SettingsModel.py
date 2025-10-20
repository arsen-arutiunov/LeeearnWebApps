from sqlalchemy import Column, UUID, ForeignKey, func, String, Boolean

from app.Infrastructure.Database import Base


class TicketFlowSettings(Base):
    __tablename__ = 'TicketFlow_Settings'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    branch_id = Column(UUID(as_uuid=True), ForeignKey('Branches.id'))

    is_telegram_bot_enabled = Column(Boolean, default=False)
    telegram_bot_name = Column(String(255), nullable=True)
    telegram_bot_token = Column(String(255), nullable=True)