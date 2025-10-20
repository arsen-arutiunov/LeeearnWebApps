from fastapi import APIRouter

v1_router = APIRouter(prefix="/v1")

from .Auth import auth_router
v1_router.include_router(auth_router)

from .Webapps import webapps_router
v1_router.include_router(webapps_router)

from .TelegramBots import bots_router
v1_router.include_router(bots_router)
