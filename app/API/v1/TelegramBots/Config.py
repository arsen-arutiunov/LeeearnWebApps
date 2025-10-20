import uuid
import asyncio
from fastapi import APIRouter, Depends, Body, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.Infrastructure.Database import getdb
from app.Services.BotManagerService import BotManager
from app.Services.BotManagerService.TelegramBotConfigService import \
    TelegramBotConfigService

config_router = APIRouter(prefix="/Config")


# Pydantic модель для валидации
class BotConfigUpdate(BaseModel):
    is_enabled: bool | None = None
    bot_name: str | None = None
    bot_token: str | None = None
    welcome_message: str | None = None


@config_router.get("/stats")
async def get_bots_stats(request: Request):
    """
    Статистика запущенных ботов.

    ВАЖНО: Этот эндпоинт должен быть ДО /{school_id},
    иначе FastAPI попытается интерпретировать 'stats' как UUID.
    """
    bot_manager: BotManager = request.app.state.bot_manager

    running_bots = []
    stopped_bots = []

    for school_id, bot_data in bot_manager.running_bots.items():
        bot_info = {
            "school_id": school_id,
            "bot_name": bot_data.get("config", {}).get("bot_name", "Unknown"),
            "is_running": not bot_data["task"].done()
        }

        if bot_info["is_running"]:
            running_bots.append(bot_info)
        else:
            stopped_bots.append(bot_info)

    return {
        "total_bots": len(bot_manager.running_bots),
        "running_count": len(running_bots),
        "stopped_count": len(stopped_bots),
        "running_bots": running_bots,
        "stopped_bots": stopped_bots
    }


@config_router.get("/{school_id}")
async def get_bot_config(school_id: uuid.UUID,
                         db: AsyncSession = Depends(getdb)):
    """
    Получает текущие настройки бота для школы (school_id).
    """
    config = await TelegramBotConfigService(db).Get(school_id)
    if not config:
        # Если конфига нет, создаем и возвращаем дефолтный
        return await TelegramBotConfigService(db).UpdateOrCreate(school_id, {})
    return config


@config_router.post("/{school_id}")
async def update_bot_config(
        school_id: uuid.UUID,
        request: Request,
        settings: BotConfigUpdate,
        db: AsyncSession = Depends(getdb)
):
    """
    Обновляет настройки бота и *перезапускает* его.
    """
    # 1. Обновляем данные в БД
    service = TelegramBotConfigService(db)
    updated_config_model = await service.UpdateOrCreate(
        school_id,
        settings.model_dump(exclude_unset=True)
    )

    # 2. Получаем Менеджер Ботов
    bot_manager: BotManager = request.app.state.bot_manager

    # 3. Конвертируем модель в dict для менеджера
    config_dict = {
        "school_id": str(updated_config_model.school_id),
        "is_enabled": updated_config_model.is_enabled,
        "bot_name": updated_config_model.bot_name,
        "bot_token": updated_config_model.bot_token,
        "welcome_message": updated_config_model.welcome_message
    }

    # 4. ВАЖНО: Ждем завершения перезапуска (убрали asyncio.create_task!)
    restart_result = await bot_manager.restart_bot(config_dict)

    return {
        "config": updated_config_model,
        "restart_status": restart_result
    }


@config_router.get("/{school_id}/status")
async def get_bot_status(
        school_id: uuid.UUID,
        request: Request
):
    """Проверяет, запущен ли бот"""
    bot_manager: BotManager = request.app.state.bot_manager
    school_id_str = str(school_id)

    if school_id_str not in bot_manager.running_bots:
        return {"status": "stopped", "school_id": school_id_str}

    bot_data = bot_manager.running_bots[school_id_str]
    is_running = not bot_data["task"].done()

    return {
        "status": "running" if is_running else "stopped",
        "school_id": school_id_str,
        "bot_name": bot_data.get("config", {}).get("bot_name")
    }
