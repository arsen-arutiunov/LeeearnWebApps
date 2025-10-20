import enum

from sqlalchemy import ARRAY, Column, UUID, String, BigInteger, func, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ENUM

from app.Infrastructure.Database import Base


class TicketStatus(enum.Enum):
    new = 1
    in_progress = 2
    done = 3
    archived = 0

class Ticket(Base):
    __tablename__ = "TicketFlow_Tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    public_id = Column(BigInteger, unique=False, nullable=False)

    author_id = Column(UUID(as_uuid=True), ForeignKey("Users.id"), nullable=False)

    assigned_roles = Column(ARRAY(UUID(as_uuid=True)), default=[])

    theme = Column(String(200), nullable=False)
    data = Column(JSONB, default=dict)
    status = Column(ENUM(TicketStatus), default=TicketStatus.new)

    leeearn_entity_type = Column(String(50), nullable=True)
    leeearn_entity_id = Column(UUID(as_uuid=True), nullable=True)

    taken_for = Column(BigInteger, nullable=True)
    done_for = Column(BigInteger, nullable=True)

    taken_at = Column(DateTime(timezone=True), nullable=True)
    done_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
