import os
from datetime import timedelta, datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.Services import get_now
from app.Services.BotManagerService.Templates.Markup import Markup
from app.Services.BotManagerService.Templates.Text import Text
from app.Services.LeeearnService.PlatformClient import PlatformClient
from dotenv import load_dotenv


load_dotenv()
PLATFORM_API_URL = os.getenv("PLATFORM_API_URL")
MAIN_PLATFORMA_API_ID = os.getenv("MAIN_PLATFORMA_API_ID")
MAIN_PLATFORMA_API_ACCESS_TOKEN = os.getenv("MAIN_PLATFORMA_API_ACCESS_TOKEN")
COMPANY_BRANCH_ID = "0938cb91-f780-401a-b18c-f88f34f3fa80"


def create_teacher_router_schedule() -> Router:
    teacher_router_schedule = Router()

    @teacher_router_schedule.callback_query(
        F.data.in_(["start_schedule", "start_schedule_tomorrow"])
    )
    async def teacher_show_schedule(callback: CallbackQuery,
                                    state: FSMContext,
                                    db: AsyncSession):
        current_time = await get_now()
        is_tomorrow = callback.data == "start_schedule_tomorrow"

        target_date = (current_time + timedelta(days=1)) if is_tomorrow else current_time
        date_text = "завтра" if is_tomorrow else "сьогодні"

        await callback.answer()

        await callback.message.edit_caption(
            caption=await Text.schedule_waiting()
        )

        lessons = await get_schedule(target_date.strftime("%Y-%m-%d"))

        if lessons:
            schedule_text = "\n\n".join(
                [f"{lesson['lesson_name']} | "
                 f"{lesson['start_time']} - "
                 f"{lesson['end_time']}" for lesson in lessons]
            )
            schedule_text = f"🗓️ Ваш розклад на {date_text}.\n\n{schedule_text}"
        else:
            schedule_text = await Text.schedule(
                target_date.strftime("%d.%m.%Y"),
                f"<i>У вас {date_text} немає уроків.</i>", "",
                date_text.capitalize()
            )
        await callback.message.edit_caption(caption=schedule_text,
                                            reply_markup=await Markup.schedule_menu(),
                                            parse_mode="html")
        print(await state.get_data())
    return teacher_router_schedule


async def get_schedule(target_date: str):
    client = PlatformClient(
        PLATFORM_API_URL,
        MAIN_PLATFORMA_API_ID,
        MAIN_PLATFORMA_API_ACCESS_TOKEN
    )
    client.debug_logs = True
    branch = client.GetBranch(COMPANY_BRANCH_ID)

    response = await branch.Teachers.GetScheduleItemList(
        teacher_id="61cbda1b-844b-4d6b-86b8-3fe8687628ee"
    )

    all_data = response.json()

    schedule_items = all_data.get('data', {}).get('data', [])

    formatted_schedule = []

    for item in schedule_items:
        item_date_str = item.get('date')

        if item_date_str and item_date_str.startswith(target_date):

            try:
                lesson_name = item.get('lesson', {}).get('name', 'Без назви')
                start_dt = datetime.fromisoformat(item_date_str)
                start_dt_adjusted = start_dt + timedelta(hours=2)
                start_time_formatted = start_dt_adjusted.strftime('%H:%M')

                end_time_formatted = "--:--"  # <-- Заглушка по умолчанию
                end_date_str = item.get('endDate')

                if end_date_str:
                    try:
                        end_dt = datetime.fromisoformat(end_date_str)
                        end_dt_adjusted = end_dt + timedelta(hours=2)
                        end_time_formatted = end_dt_adjusted.strftime('%H:%M')
                    except ValueError:
                        pass

                formatted_schedule.append({
                    'lesson_name': lesson_name,
                    'start_time': start_time_formatted,
                    'end_time': end_time_formatted
                })

            except Exception as e:
                print(
                    f"Ошибка обработки занятия (id: {item.get('id')}). Невалидная start_date: {e}")

    return formatted_schedule
