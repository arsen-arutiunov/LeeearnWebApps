from aiogram import Dispatcher, Router
from aiogram.filters import CommandStart

from app.Services.BotManagerService.Handlers.StartHandler import (
    create_router_start
)

def create_main_router() -> Router:
    router = Router()
    router.include_router(create_router_start())
    return router
