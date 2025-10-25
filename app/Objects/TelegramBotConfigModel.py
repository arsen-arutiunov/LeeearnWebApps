from sqlalchemy import Column, UUID, func, String, Boolean, Text

from app.Infrastructure.Database import Base


class TelegramBotConfig(Base):
    """
    Хранит независимые настройки Telegram бота для
    конкретного school_id (школы).
    """
    __tablename__ = 'TelegramBot_Configs'

    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default=func.gen_random_uuid())

    # Идентификатор школы (не связанный, по вашему запросу)
    school_id = Column(UUID(as_uuid=True), unique=True, nullable=False,
                       index=True)

    # --- Настройки бота ---
    is_enabled = Column(Boolean, default=False, nullable=False)
    bot_name = Column(String(255), nullable=True, default="Бот")

    # ВАЖНО: В реальном проекте храните токен в шифрованном виде
    bot_token = Column(String(255), nullable=True)

    # --- Шаблоны сообщений ---
    welcome_message = Column(Text, nullable=True, default="Привет! 👋")

    image_url = Column(String(255), nullable=True)

    # ... можно добавить и другие шаблоны ...