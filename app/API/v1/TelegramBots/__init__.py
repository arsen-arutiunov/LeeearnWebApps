from fastapi import APIRouter

bots_router = APIRouter(prefix="/Bots", tags=["Telegram Bots"])

from .Config import config_router
bots_router.include_router(config_router)