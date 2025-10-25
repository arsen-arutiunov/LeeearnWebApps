from datetime import timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.Services import get_now
from app.Services.BotManagerService.Templates.Markup import Markup
from app.Services.BotManagerService.Templates.Text import Text


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

        schedule_text = await Text.schedule(
            target_date.strftime("%d.%m.%Y"),
            f"<i>У вас {date_text} немає уроків.</i>", "",
            date_text.capitalize()
        )
        await callback.message.edit_caption(caption=schedule_text,
                                            reply_markup=await Markup.schedule_menu(),
                                            parse_mode="html")

    return teacher_router_schedule
