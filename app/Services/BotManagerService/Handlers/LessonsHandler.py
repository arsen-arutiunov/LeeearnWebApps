import os
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.Services.BotManagerService.Templates.Markup import Markup
from app.Services.BotManagerService.Templates.Text import Text
from app.Services.LeeearnService.PlatformClient import PlatformClient
from dotenv import load_dotenv

from app.Services.ModelServices.UserService import get_user_by_telegram_id

load_dotenv()
PLATFORM_API_URL = os.getenv("PLATFORM_API_URL")
MAIN_PLATFORMA_API_ID = os.getenv("MAIN_PLATFORMA_API_ID")
MAIN_PLATFORMA_API_ACCESS_TOKEN = os.getenv("MAIN_PLATFORMA_API_ACCESS_TOKEN")


def create_teacher_router_lessons() -> Router:
    teacher_router_lessons = Router()

    @teacher_router_lessons.callback_query(lambda c: c.data == "start_lessons")
    async def show_schedule(callback: CallbackQuery,
                            state: FSMContext,
                            db: AsyncSession):
        await callback.message.edit_caption(
            caption=await Text.lessons(),
            reply_markup=await Markup.lessons_menu(),
            parse_mode="html"
        )

    @teacher_router_lessons.callback_query(lambda c: c.data == "lesson_move_accept")
    async def lesson_move_accept(callback: CallbackQuery, state: FSMContext):
        """Обирає день для переносу уроку."""
        await callback.message.edit_caption(
            caption="⚠️ Цю кнопочку натискаємо тільки тоді, коли "
                    "ви з учнем узгодили перенос уроку. Тобто коли "
                    "клієнт знає про те, що урок буде перенесено.",
            reply_markup=await Markup.move_lesson_acceptation()
        )

    async def get_upcoming_lessons(branch_id: str, teacher_id: str):
        """
        Возвращает два списка:
          1️⃣ upcoming_lessons — список будущих уроков на неделю вперед (не включая текущие).
          2️⃣ lesson_days — уникальные даты (дни), на которые есть уроки.
        Учитывает сдвиг +2 часа.
        """
        client = PlatformClient(
            PLATFORM_API_URL,
            MAIN_PLATFORMA_API_ID,
            MAIN_PLATFORMA_API_ACCESS_TOKEN
        )
        client.debug_logs = True
        branch = client.GetBranch(branch_id)

        response = await branch.Teachers.GetScheduleItemList(
            teacher_id=teacher_id
        )

        all_data = response.json()
        schedule_items = all_data.get('data', {}).get('data', [])

        now = datetime.now()
        one_week_ahead = now + timedelta(days=7)

        upcoming_lessons = []
        lesson_days = set()  # тимчасово зберігаємо унікальні дати

        for item in schedule_items:
            item_date_str = item.get('date')
            end_date_str = item.get('endDate')

            if not item_date_str or not end_date_str:
                continue

            try:
                start_dt = datetime.fromisoformat(item_date_str)
                end_dt = datetime.fromisoformat(end_date_str)

                # Додаємо +2 години (враховуємо різницю з платформою)
                start_dt += timedelta(hours=2)
                end_dt += timedelta(hours=2)

                # Фільтруємо: урок має бути в майбутньому і не далі ніж через 7 днів
                if start_dt > now and start_dt <= one_week_ahead:
                    lesson_name = item.get('lesson', {}).get('name',
                                                             'Без назви')

                    upcoming_lessons.append({
                        "lesson_id": item.get('id'),
                        'lesson_name': lesson_name,
                        'start_time': start_dt.strftime('%Y-%m-%d %H:%M'),
                        'end_time': end_dt.strftime('%Y-%m-%d %H:%M')
                    })

                    # Зберігаємо дату (лише день)
                    lesson_days.add(start_dt.date())

            except Exception as e:
                if "year 0 is out of range" in str(e):
                    print(
                        f"Пропущено занятие (id: {item.get('id')}) с невалидной датой.")
                else:
                    print(
                        f"Ошибка обработки занятия (id: {item.get('id')}): {e}")

        # Сортуємо за часом початку
        upcoming_lessons.sort(key=lambda x: x['start_time'])

        # Перетворюємо множину у список і сортуємо по даті
        lesson_days = sorted([d.strftime('%Y-%m-%d') for d in lesson_days])

        return upcoming_lessons, lesson_days

    @teacher_router_lessons.callback_query(F.data == "lesson_move")
    async def lesson_move(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
        user = await get_user_by_telegram_id(db, callback.from_user.id,
                                             with_roles=True)
        upcoming_lessons, lesson_days = await get_upcoming_lessons(
            user.branch_id,
            user.id
        )
        if len(upcoming_lessons) == 0 or len(lesson_days) == 0:
            await callback.message.edit_caption(
                caption="❌ Ви не можете подати запит на перенос, оскільки у вас немає уроків.",
                reply_markup=await Markup.lessons_menu()
            )
            return

        if len(lesson_days) > 1:
            await callback.message.edit_caption(
                caption="Оберіть дату:",
                reply_markup=await Markup.choose_date(lesson_days)
            )
        else:
            if len(lesson_days) == 1:
                lessons_for_date = []

                for lesson in upcoming_lessons:
                    # Извлекаем дату начала (первая часть 'YYYY-MM-DD HH:MM')
                    start_date_str = lesson['start_time'].split(' ')[0]

                    if start_date_str == lesson_days[0]:
                        lessons_for_date.append(lesson)

                lessons_for_date.sort(key=lambda x: x['start_time'])

                await callback.message.edit_caption(
                    caption="Оберіть урок:",
                    reply_markup=await Markup.choose_lesson(lessons_for_date)
                )

    @teacher_router_lessons.callback_query(F.data.startswith("choose_lesson:"))
    async def choose_lesson(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
        lesson_id = callback.data.split(":")[1]

        #TODO тут будет реализован процес получения даты для переноса урока

    @teacher_router_lessons.callback_query(F.data.startswith("choose_date:"))
    async def choose_date(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
        date = callback.data.split(":")[1]
        user = await get_user_by_telegram_id(db, callback.from_user.id,
                                             with_roles=True)
        upcoming_lessons, lesson_days = await get_upcoming_lessons(
            user.branch_id,
            user.id
        )
        lessons_for_date = []

        for lesson in upcoming_lessons:
            # Извлекаем дату начала (первая часть 'YYYY-MM-DD HH:MM')
            start_date_str = lesson['start_time'].split(' ')[0]

            if start_date_str == date:
                lessons_for_date.append(lesson)

        lessons_for_date.sort(key=lambda x: x['start_time'])

        await callback.message.edit_caption(
            caption="Оберіть урок:",
            reply_markup=await Markup.choose_lesson(lessons_for_date)
        )

    async def get_current_lesson(branch_id: str, teacher_id: str):
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

        response = await branch.Teachers.GetScheduleItemList(
            teacher_id=teacher_id
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
                        "lesson_id": item.get('id'),
                        'lesson_name': lesson_name,
                        'start_time': start_dt.strftime('%H:%M'),
                        'end_time': end_dt.strftime('%H:%M')
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

    @teacher_router_lessons.callback_query(lambda c: c.data == "lesson_nopupil")
    async def lesson_nopupil(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
        user = await get_user_by_telegram_id(db, callback.from_user.id, with_roles=True)
        lesson = await get_current_lesson(
            branch_id=user.branch_id,
            teacher_id=user.id,
        )

        if not lesson:
            await callback.message.edit_caption(
                caption="❌ Ви не можете подати запит, оскільки у вас зараз немає активного уроку.",
                reply_markup=await Markup.lessons_menu()
            )
            return

        await callback.message.edit_caption(
            caption=f"Підтвердження відсутності учня на уроці.\n\n"
                    f"Урок:\n{lesson['lesson_name']} | "
                    f"{lesson['start_time']} - {lesson['end_time']}",
            reply_markup=await Markup.lesson_nopupil_confirm(lesson["lesson_id"])
        )
        return

    @teacher_router_lessons.callback_query(F.data.startswith("confirm_lesson:"))
    async def confirm_lesson(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
        lesson_id = callback.data.split(":")
        #TODO: тут будет фиксация что ученика нет

        await callback.message.edit_caption(
            caption="Дякуємо за звіт. Інформація збережена.",
            reply_markup=await Markup.lessons_menu()
        )

    return teacher_router_lessons
