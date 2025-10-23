import random
import uuid

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.Objects.BranchRoleModel import BranchRole
from app.Objects.UserModel import User
from app.Services.BotManagerService.Templates.Markup import Markup
from app.Services.BotManagerService.Templates.Text import Text
from app.Services.ModelServices.BranchRoleServices import get_role_by_id
from app.Services.ModelServices.UserService import (
    get_user_by_telegram_id,
    get_user_roles,
)


# Список эмодзи для случайного выбора
emojis = ["✌️", "✋", "🤝", "👋", "🙌"]

# Абсолютный путь к файлу изображения
photo_url = "https://lumeriq.b-cdn.net/public-osvitech/start_menu_image.jpeg"
file_id = None  # Переменная для хранения file_id


# ----- Основная функция действия -----
async def action(session: AsyncSession,
                 message: Message,
                 state: FSMContext,
                 user: User,
                 role: BranchRole,
                 branch_id: uuid.UUID):

    hi_emoji = random.choice(emojis)
    if user.branch_id == branch_id and role.branch_id == branch_id and role in user.roles:
        if role.name == "Вчитель":
            # TODO реализовать функционал дальше
            msg = await message.answer_photo(
                photo=photo_url,
                caption=await Text.start_success_teacher(hi_emoji, user.name),
                parse_mode="html",
                reply_markup=await Markup.start_menu()
            )
        elif role.name == "Куратор":
            #TODO реализовать кураторский функционал (будущее)
            msg = await message.answer("Тут будет контент для куратора")
    # здесь можешь запустить логику нужной роли (например, меню или обработчик)
    # ...

def create_router_start() -> Router:
    router = Router()
    @router.message(F.text == "/start", F.chat.type == "private")
    async def start_handler(
            message: Message,
            state: FSMContext,
            config: dict,  # <-- Наш конфиг (в нем 'school_id' и 'welcome_message')
            db: AsyncSession
    ):
        user_id = message.from_user.id
        hi_emoji = random.choice(emojis)

        await state.clear()

        branch_id = uuid.UUID(config.get("school_id"))

        user = await get_user_by_telegram_id(db, telegram_id=user_id)

        if user is None or user.branch_id != branch_id:
            await message.answer("❌ Ви не маєте доступу до цього боту.")
            return

        roles = await get_user_roles(db, user_id=user.id)

        # Если ролей нет
        if not roles:
            await message.answer("⚠️ У вас ще не призначено ролей.")
            return

        if len(roles) == 1:
            await state.update_data(role_id=roles[0].id, user_id=user.id)
            await action(db, message, state, user, roles[0], branch_id)
            return
        await state.update_data(branch_id=branch_id, user_id=user.id)
        await message.answer(
            text=f"{hi_emoji} Оберіть роль, під якою ви хочете увійти:",
            reply_markup=await Markup.select_role(user, roles)
        )


    @router.callback_query(lambda c: c.data.startswith("select_role:"))
    async def select_role_callback(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
        callback_data = callback.data.split(":")
        role_id = uuid.UUID(callback_data[1])
        telegram_id = callback.from_user.id

        # Получаем роль из БД (если хочешь имя)
        role = await get_role_by_id(db, role_id)
        user = await get_user_by_telegram_id(db, telegram_id, with_roles=True)
        branch_id = user.branch_id

        await state.update_data(role_name=role.name, role_id=str(role.id))

        await callback.message.edit_text(
            text=f"✅ Ви увійшли як <b>{role.name}</b>",
            parse_mode="HTML",
            reply_markup=None
        )

        # Запускаем основное действие
        await action(db, callback.message, state, user, role, branch_id)

    return router