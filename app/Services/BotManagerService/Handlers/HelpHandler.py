from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.Services.BotManagerService.Templates.Markup import Markup
from app.Services.BotManagerService.Templates.Text import Text


def create_teacher_router_help() -> Router:
    teacher_router_help = Router()

    @teacher_router_help.callback_query(lambda c: c.data == "start_help")
    async def start_help(callback: CallbackQuery,
                         state: FSMContext,
                         db: AsyncSession):
        #TODO: согласовать как будет работать блок помощи
        await callback.message.edit_caption(
            caption=await Text.start_help(),
            reply_markup=await Markup.start_help(
                f"https://t.me/example",
                1
            ),
            parse_mode="html"
        )

    return teacher_router_help
