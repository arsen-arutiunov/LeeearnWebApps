import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.Objects.TelegramBotConfigModel import TelegramBotConfig


class TelegramBotConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def Get(self, school_id: uuid.UUID) -> TelegramBotConfig | None:
        """
        Получает конфиг бота по school_id.
        """
        result = await self.db.execute(
            select(TelegramBotConfig).where(TelegramBotConfig.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def UpdateOrCreate(self, school_id: uuid.UUID, settings_data: dict) -> TelegramBotConfig:
        """
        Обновляет или создает конфиг бота для school_id.
        """
        result = await self.db.execute(
            select(TelegramBotConfig).where(TelegramBotConfig.school_id == school_id)
        )
        db_config = result.scalar_one_or_none()

        if db_config:
            # Обновляем существующий
            for key, value in settings_data.items():
                if hasattr(db_config, key):
                    setattr(db_config, key, value)
        else:
            db_config = TelegramBotConfig(**settings_data)
            # Создаем новый
            db_config = TelegramBotConfig(school_id=school_id, **settings_data)
            self.db.add(db_config)

        await self.db.commit()
        await self.db.refresh(db_config)
        return db_config

    async def GetAllEnabled(self) -> Sequence[TelegramBotConfig]:
        """
        Получает ВСЕ конфиги ботов, у которых стоит is_enabled = True.
        """
        result = await self.db.execute(
            select(TelegramBotConfig).where(TelegramBotConfig.is_enabled == True)
        )
        return result.scalars().all()