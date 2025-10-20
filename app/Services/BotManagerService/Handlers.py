import logging
from aiogram import Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession


def register_handlers(dp: Dispatcher):
    dp.message.register(start_handler, CommandStart())
    dp.message.register(any_text_handler)


async def start_handler(
        message: Message,
        config: dict,  # <-- Наш конфиг (в нем 'school_id' и 'welcome_message')
        db: AsyncSession
):
    welcome_text = config.get("welcome_message", "Привет!")
    await message.answer(welcome_text)


async def any_text_handler(
        message: Message,
        config: dict,
        db: AsyncSession
):
    bot_name = config.get("bot_name", "Бот")
    school_id = config.get("school_id")

    logging.info(
        f"Получено сообщение для {school_id} от {message.from_user.id}")

    await message.answer(
        f"[{bot_name}]: Ваше сообщение '{message.text}' получено.\n"
        f"(ID школы: {school_id})"
    )