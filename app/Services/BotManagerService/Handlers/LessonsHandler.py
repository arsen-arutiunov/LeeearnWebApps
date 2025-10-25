from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.Services.BotManagerService.Templates.Markup import Markup
from app.Services.BotManagerService.Templates.Text import Text


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

    return teacher_router_lessons
