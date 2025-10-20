import asyncio
import logging
from typing import Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.Infrastructure.Database import async_session
from .Handlers import register_handlers
from .Middleware import DbSessionMiddleware


class BotManager:
    def __init__(self):
        """
        Храним словарь с запущенными ботами.
        Ключ - school_id, значение - dict с task, dispatcher, bot и stop_event.
        """
        self.running_bots: Dict[str, Dict[str, Any]] = {}
        logging.info("🤖 BotManager инициализирован.")

    async def _run_bot_polling(self, dp: Dispatcher, bot: Bot, config: dict,
                               stop_event: asyncio.Event):
        """
        Внутренний метод для запуска поллинга с возможностью остановки.
        """
        school_id = config.get("school_id")
        bot_name = config.get("bot_name", f"Bot {school_id}")

        # Передаем пул сессий БД в middleware
        dp.update.middleware(DbSessionMiddleware(session_pool=async_session))

        logging.info(
            f"🚀 Запуск поллинга для бота: {bot_name} (school_id: {school_id})")

        try:
            # Запускаем поллинг с передачей stop_event
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                config=config,
                handle_signals=False
                # Важно! Не перехватываем системные сигналы
            )
        except asyncio.CancelledError:
            logging.info(f"🛑 Поллинг отменен для: {bot_name}")
        except Exception as e:
            logging.error(f"❌ Ошибка в цикле поллинга {bot_name}: {e}",
                          exc_info=True)
        finally:
            logging.info(f"✅ Поллинг-цикл завершен для: {bot_name}")

    async def start_bot(self, config: dict):
        """
        Запускает новый экземпляр бота.
        """
        school_id = str(config["school_id"])
        token = config.get("bot_token")

        if not token:
            logging.warning(
                f"⚠️ Нет токена для school_id: {school_id}. Бот не запущен.")
            return {"status": "no_token", "school_id": school_id}

        # Проверяем, что бот УЖЕ НЕ ЗАПУЩЕН
        if school_id in self.running_bots:
            bot_data = self.running_bots[school_id]
            if not bot_data["task"].done():
                logging.info(f"ℹ️ Бот для {school_id} уже запущен.")
                return {"status": "already_running", "school_id": school_id}

        logging.info(f"🔧 Создание бота для school_id: {school_id}")

        # Создаем объекты
        bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()
        stop_event = asyncio.Event()

        # Регистрируем хэндлеры
        register_handlers(dp)

        # Создаем задачу
        task = asyncio.create_task(
            self._run_bot_polling(dp, bot, config, stop_event)
        )

        # Сохраняем ВСЕ объекты
        self.running_bots[school_id] = {
            "task": task,
            "dispatcher": dp,
            "bot": bot,
            "stop_event": stop_event,
            "config": config  # Сохраняем конфиг для доступа к bot_name и т.д.
        }

        logging.info(f"✅ Бот для {school_id} запущен успешно")
        return {"status": "started", "school_id": school_id}

    async def stop_bot(self, school_id: str):
        """
        Корректно останавливает работающий бот.
        """
        school_id = str(school_id)
        bot_instance = self.running_bots.get(school_id)

        # Проверяем, есть ли что останавливать
        if not bot_instance:
            logging.info(
                f"ℹ️ Бот для {school_id} не найден в списке запущенных.")
            return {"status": "not_found", "school_id": school_id}

        task: asyncio.Task = bot_instance["task"]

        if task.done():
            logging.info(f"ℹ️ Бот для {school_id} уже остановлен.")
            # Очищаем из словаря
            del self.running_bots[school_id]
            return {"status": "already_stopped", "school_id": school_id}

        logging.info(f"🛑 Начинаем остановку бота для {school_id}...")

        dispatcher: Dispatcher = bot_instance["dispatcher"]
        bot: Bot = bot_instance["bot"]
        stop_event: asyncio.Event = bot_instance["stop_event"]

        try:
            # 1. Устанавливаем флаг остановки
            stop_event.set()

            # 2. Останавливаем диспетчер (прекращает обработку новых обновлений)
            await dispatcher.stop_polling()

            logging.info(
                f"⏳ Ожидание завершения задачи поллинга для {school_id}...")

            # 3. Ждем завершения задачи с таймаутом
            await asyncio.wait_for(task, timeout=10.0)

            logging.info(f"✅ Задача поллинга для {school_id} завершена")

        except asyncio.TimeoutError:
            logging.warning(
                f"⚠️ Таймаут остановки для {school_id}. Принудительная отмена...")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logging.info(
                    f"✅ Задача для {school_id} принудительно отменена")

        except Exception as e:
            logging.error(f"❌ Ошибка при остановке бота {school_id}: {e}",
                          exc_info=True)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        finally:
            # 4. Закрываем HTTP-сессию бота
            try:
                await bot.session.close()
                logging.info(f"✅ HTTP сессия для {school_id} закрыта")
            except Exception as e:
                logging.error(f"❌ Ошибка закрытия сессии {school_id}: {e}")

            # 5. Удаляем из списка запущенных
            if school_id in self.running_bots:
                del self.running_bots[school_id]
                logging.info(f"✅ Бот {school_id} удален из списка запущенных")

        return {"status": "stopped", "school_id": school_id}

    async def restart_bot(self, config: dict):
        """
        Перезапускает бота (останавливает + запускает заново).
        """
        school_id = str(config["school_id"])
        logging.info(f"🔄 Перезапуск бота для {school_id}...")

        # 1. Останавливаем текущий бот
        stop_result = await self.stop_bot(school_id)
        logging.info(f"   Результат остановки: {stop_result['status']}")

        # 2. Небольшая пауза для полного завершения
        await asyncio.sleep(0.5)

        # 3. Запускаем заново, только если бот включен
        if config.get("is_enabled"):
            logging.info(f"   ▶️ Запуск бота для {school_id}...")
            start_result = await self.start_bot(config)
            logging.info(f"   Результат запуска: {start_result['status']}")
            return start_result
        else:
            logging.info(
                f"   ⏸️ Бот {school_id} остановлен и не включен (is_enabled=False)")
            return {"status": "stopped_disabled", "school_id": school_id}

    async def stop_all_bots(self):
        """
        Останавливает всех запущенных ботов при выключении FastAPI.
        """
        if not self.running_bots:
            logging.info("ℹ️ Нет активных ботов для остановки")
            return

        logging.info(
            f"🛑 Остановка всех активных ботов ({len(self.running_bots)})...")

        # Создаем список задач на остановку
        school_ids = list(self.running_bots.keys())
        tasks = [self.stop_bot(school_id) for school_id in school_ids]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Логируем результаты
        for school_id, result in zip(school_ids, results):
            if isinstance(result, Exception):
                logging.error(f"❌ Ошибка остановки бота {school_id}: {result}")
            else:
                logging.info(f"✅ Бот {school_id} остановлен: {result}")

        logging.info("✅ Все боты остановлены")
