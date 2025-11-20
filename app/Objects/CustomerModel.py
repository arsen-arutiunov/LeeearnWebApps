from sqlalchemy import Column, UUID, ForeignKey, String

from app.Infrastructure.Database import Base


class Customer(Base):
    __tablename__ = "Customers"
    __table_args__ = {"schema": "auth"}

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('auth."Users".id', ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    leeearn_id = Column(UUID(as_uuid=True))
    name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(100))