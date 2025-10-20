import enum

from sqlalchemy import Column, UUID, String, Boolean, Integer, func, TIMESTAMP, DateTime
from sqlalchemy.dialects.postgresql import JSONB, ENUM

from app.Infrastructure.Database import Base


class TicketFieldType(str, enum.Enum):
    text = "text"
    textarea = "textarea"
    select = "select"
    checkbox = "checkbox"
    date = "date"
    datetime = "datetime"
    smartselect = "smartselect"
    daterange = "daterange"

class TicketField(Base):
    __tablename__ = "TicketFlow_TicketFields"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    key = Column(String(64), unique=True, nullable=False)

    label = Column(String(200), nullable=False)
    type = Column(ENUM(TicketFieldType), nullable=False)

    required = Column(Boolean, default=False)
    order = Column(Integer, default=0, nullable=False)

    config = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())