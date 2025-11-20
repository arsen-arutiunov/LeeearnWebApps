import os
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiohttp import web
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.Services.BotManagerService.Templates.CustomerMarkup import \
    CustomerMarkup
from app.Services.BotManagerService.Templates.TeacherMarkup import \
    TeacherMarkup
from app.Services.LeeearnService.PlatformClient import PlatformClient
from app.Services.ModelServices.CustomerService import get_customer_by_user_id
from app.Services.ModelServices.UserService import get_user_by_telegram_id

load_dotenv()
PLATFORM_API_URL = os.getenv("PLATFORM_API_URL")
MAIN_PLATFORMA_API_ID = os.getenv("MAIN_PLATFORMA_API_ID")
MAIN_PLATFORMA_API_ACCESS_TOKEN = os.getenv("MAIN_PLATFORMA_API_ACCESS_TOKEN")

default_photo_url = "https://staticstorage.leeearn.ai/apps/student_bot/student_management_bot.png"


def customer_menu_handler() -> Router:
    customer_menu_router = Router()

    @customer_menu_router.callback_query(lambda c: c.data == "my_balance")
    async def my_balance(callback: CallbackQuery,
                         state: FSMContext,
                         db: AsyncSession):
        await callback.message.edit_caption(
            caption="Тут буде баланс учня",
            reply_markup=await CustomerMarkup.back_to_customers_menu()
        )

    @customer_menu_router.callback_query(lambda c: c.data == "social_networks")
    async def social_networks(callback: CallbackQuery,
                              state: FSMContext,
                              db: AsyncSession):
        social_networks = {
            "Посилання 1": "https://example.com",
            "Посилання 2": "https://example.com",
            "Посилання 3": "https://example.com",
        }
        await callback.message.edit_caption(
            caption="",
            reply_markup=await CustomerMarkup.social_networks_menu(
                social_networks)
        )

    async def get_current_lesson(branch_id: str, customer_id: str):
        """
        Возвращает текущий урок (если он идёт прямо сейчас) или None.
        Учитывает сдвиг +2 часа между локальным временем и временем из платформы.
        """
        client = PlatformClient(
            PLATFORM_API_URL,
            MAIN_PLATFORMA_API_ID,
            MAIN_PLATFORMA_API_ACCESS_TOKEN
        )
        client.debug_logs = True
        branch = client.GetBranch(branch_id)

        response = await branch.Customers.GetScheduleItemList(
            customer_id=customer_id
        )

        all_data = response.json()
        schedule_items = all_data.get('data', {}).get('data', [])

        # Текущее локальное время (с учётом сдвига)
        now = datetime.now()
        now = datetime(2025, 11, 6, 16, 10, 0)

        for item in schedule_items:
            item_date_str = item.get('date')
            end_date_str = item.get('endDate')

            if not item_date_str or not end_date_str:
                continue

            try:
                start_dt = datetime.fromisoformat(item_date_str)
                end_dt = datetime.fromisoformat(end_date_str)

                # Добавляем +2 часа для выравнивания с нашим временем
                start_dt += timedelta(hours=2)
                end_dt += timedelta(hours=2)

                # Проверяем, попадает ли текущее время в этот диапазон
                if start_dt <= now <= end_dt:
                    lesson_name = item.get('lesson', {}).get('name',
                                                             'Без назви')

                    return {
                        "group": item.get("group", None).get("id", None),
                        "lesson_id": item.get('id'),
                        'lesson_name': lesson_name,
                        'start_time': start_dt.strftime('%H:%M'),
                        'end_time': end_dt.strftime('%H:%M'),
                    }

            except Exception as e:
                if "year 0 is out of range" in str(e):
                    print(
                        f"Пропущено занятие (id: {item.get('id')}) с невалидной датой.")
                else:
                    print(
                        f"Ошибка обработки занятия (id: {item.get('id')}): {e}")

        # Если ни один урок сейчас не идёт
        return None

    @customer_menu_router.callback_query(lambda c: c.data == "lesson_link")
    async def lesson_link(callback: CallbackQuery,
                          state: FSMContext,
                          db: AsyncSession):
        user = await get_user_by_telegram_id(db, callback.from_user.id,
                                             with_roles=True)

        if user is None:
            await callback.answer("Користувача не було знайдено.", show_alert=True)
            return

        lesson = await get_current_lesson(user.branch_id, user.id)
        if lesson is None:
            await callback.answer("Не знайдено активного урока.", show_alert=True)
            return

        await callback.answer()

        await callback.message.edit_caption(
            caption=f"Тут буде посилання на урок:\n\n"
                    f"{lesson['lesson_name']}\n"
                    f"{lesson['start_time']} - {lesson['end_time']}",
            reply_markup=await CustomerMarkup.back_to_customers_menu()
        )

        @customer_menu_router.callback_query(
            lambda c: c.data == "forwarding_no_lesson")
        async def forwarding_no_lesson(callback: CallbackQuery,
                                       state: FSMContext,
                                       db: AsyncSession):
            user = await get_user_by_telegram_id(db, callback.from_user.id,
                                                 with_roles=True)

            if user is None:
                await callback.answer("Користувача не було знайдено.",
                                      show_alert=True)
                return

            lesson = await get_current_lesson(user.branch_id, user.id)
            if lesson is None:
                await callback.answer("Не знайдено активного урока.",
                                      show_alert=True)
                return

            await callback.answer()

            await callback.message.edit_caption(
                caption=f"Тут буде підтвердження відсутності уроку:\n\n"
                        f"{lesson['lesson_name']}\n"
                        f"{lesson['start_time']} - {lesson['end_time']}",
                reply_markup=await CustomerMarkup.forwarding_no_lesson_menu(lesson)
            )

        @customer_menu_router.callback_query(
            lambda c: c.data == "forwarding_call_me")
        async def forwarding_call_me(callback: CallbackQuery,
                                       state: FSMContext,
                                       db: AsyncSession):
            user = await get_user_by_telegram_id(db, callback.from_user.id,
                                                 with_roles=True)

            await callback.message.edit_caption(
                caption="Підтвердження прохання подзвонити мені.",
                reply_markup=await CustomerMarkup.forwarding_call_me(user.id)
            )


    return customer_menu_router
