from sqlalchemy import Column, Integer, Boolean, Text, BigInteger, UUID, \
    ForeignKey

from app.Infrastructure.Database import Base


class Teacher(Base):
    __tablename__ = "Teachers"
    __table_args__ = {"schema": "auth"}

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('auth."Users".id', ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    # TODO: удалить или реализовать (в БД не добавил)
    # supervisor_id = Column(BigInteger, ForeignKey("teachers.supervisors.telegram_id"), nullable=True)

    additional_branch_id = Column(Integer, nullable=False, default=0)
    is_contract_accepted = Column(Boolean, nullable=False, default=False)
    contract_accepted_time = Column(Text, nullable=True)
    guide_message_id = Column(BigInteger, nullable=True)
    weekly_points = Column(Integer, nullable=True, default=0)  # баллы за неделю
    monthly_points = Column(Integer, nullable=True, default=0)  # баллы за месяц

    setting_delete_proofs = Column(Boolean, nullable=False, default=True)
    setting_report_notification = Column(Boolean, nullable=False, default=True)
    setting_time_zone = Column(Text, nullable=True)
    setting_screenshot_time_kyiv = Column(Boolean, nullable=False,
                                          default=False)