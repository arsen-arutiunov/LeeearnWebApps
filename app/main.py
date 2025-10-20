import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.API import api_router
from app.Infrastructure.Database import engine, Base, async_session

from app.Services.BotManagerService import BotManager
from app.Services.BotManagerService.TelegramBotConfigService import (
    TelegramBotConfigService
)
from app.Objects.TelegramBotConfigModel import TelegramBotConfig

load_dotenv()
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting application...")

    bot_manager = BotManager()
    app.state.bot_manager = bot_manager

    try:
        # await redis_client.connect()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logging.info("Загрузка и запуск активных ботов из БД...")
        async with async_session() as session:
            service = TelegramBotConfigService(session)
            enabled_bots_configs = await service.GetAllEnabled()

            tasks = []
            for config_model in enabled_bots_configs:
                # Конвертируем модель в dict
                config_dict = {
                    "school_id": str(config_model.school_id),
                    "is_enabled": config_model.is_enabled,
                    "bot_name": config_model.bot_name,
                    "bot_token": config_model.bot_token,
                    "welcome_message": config_model.welcome_message
                }
                tasks.append(bot_manager.start_bot(config_dict))

            await asyncio.gather(*tasks)
            logging.info(
                f"✅ Запущено {len(enabled_bots_configs)} ботов при старте.")

        yield
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        raise
    finally:
        # await redis_client.disconnect()
        logging.info("👋 Application stopping...")
        if app.state.bot_manager:
            await app.state.bot_manager.stop_all_bots()
        print("👋 Application stopped")

app = FastAPI(
    title="Leeearn Webapps API",
    description="Leeearn Webapps API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://workspace.leeearn.ai"
        "https://apps.leeearn.ai"
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "supersecretkey"),
    same_site = "lax",
    https_only = False
)

app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
