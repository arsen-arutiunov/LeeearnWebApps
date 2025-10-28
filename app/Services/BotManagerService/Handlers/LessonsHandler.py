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

    @teacher_router_lessons.callback_query(lambda c: c.data == "lesson_move_accept")
    async def lesson_move_accept(callback: CallbackQuery, state: FSMContext):
        """Обирає день для переносу уроку."""
        await callback.message.edit_caption(
            caption="⚠️ Цю кнопочку натискаємо тільки тоді, коли "
                    "ви з учнем узгодили перенос уроку. Тобто коли "
                    "клієнт знає про те, що урок буде перенесено.",
            reply_markup=await Markup.move_lesson_acceptation()
        )

    return teacher_router_lessons


