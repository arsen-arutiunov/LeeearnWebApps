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
    get_user_roles, get_user_by_id,
)

# Список эмодзи для случайного выбора
emojis = ["✌️", "✋", "🤝", "👋", "🙌"]

# Абсолютный путь к файлу изображения
#photo_url = "https://lumeriq.b-cdn.net/public-osvitech/start_menu_image.jpeg"
#second_photo_url = "https://imgpx.com/upJYdJj0lV7g"
#curator_photo_url = "https://imgpx.com/mBDN7C4gptST"

file_id = None  # Переменная для хранения file_id


# ----- Основная функция действия -----
async def action(session: AsyncSession,
                 message: Message,
                 state: FSMContext,
                 user: User,
                 role: BranchRole,
                 branch_id: uuid.UUID):
    hi_emoji = random.choice(emojis)
    data = await state.get_data()
    if user.branch_id == branch_id and role.branch_id == branch_id and role in user.roles:
        if role.name == "Вчитель":
            # TODO реализовать функционал дальше
            """if message.content_type == "text":"""
            if message.content_type == "photo":
                msg = await message.edit_caption(
                    caption=await Text.start_success_teacher(hi_emoji,
                                                             user.name),
                    parse_mode="html",
                    reply_markup=await Markup.teacher_menu()
                )
            else:
                await message.delete()
                msg = await message.answer_photo(
                    photo=data["image_url"],
                    caption=await Text.start_success_teacher(hi_emoji,
                                                             user.name),
                    parse_mode="html",
                    reply_markup=await Markup.teacher_menu()
                )

        elif role.name == "Куратор":
            # TODO реализовать кураторский функционал (будущее)
            if message.content_type == "photo":
                msg = await message.edit_caption(
                    caption="Тут будет контент для куратора",
                    parse_mode="html",
                    reply_markup=await Markup.curators_menu()
                )
            else:
                await message.delete()
                msg = await message.answer_photo(
                    photo=data["image_url"],
                    caption="Тут будет контент для куратора",
                    parse_mode="html",
                    reply_markup=await Markup.curators_menu()
                )
    # здесь можешь запустить логику нужной роли (например, меню или обработчик)
    # ...


def create_teacher_start_router() -> Router:
    teacher_start_router = Router()

    @teacher_start_router.message(F.text == "/start", F.chat.type == "private")
    async def start_handler(
            message: Message,
            state: FSMContext,
            config: dict,
            # <-- Наш конфиг (в нем 'school_id' и 'welcome_message')
            db: AsyncSession
    ):
        user_id = message.from_user.id
        hi_emoji = random.choice(emojis)

        await state.clear()

        branch_id = uuid.UUID(config.get("school_id"))
        image_url = config.get("image_url")
        await state.update_data(image_url=image_url)

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

    @teacher_start_router.callback_query(lambda c: c.data.startswith("select_role:"))
    async def select_role_callback(callback: CallbackQuery, state: FSMContext,
                                   db: AsyncSession):
        callback_data = callback.data.split(":")
        role_id = uuid.UUID(callback_data[1])
        telegram_id = callback.from_user.id

        # Получаем роль из БД (если хочешь имя)
        role = await get_role_by_id(db, role_id)
        user = await get_user_by_telegram_id(db, telegram_id, with_roles=True)
        branch_id = user.branch_id

        await state.update_data(role_name=role.name, role_id=str(role.id))

        await callback.answer(
            text=f"✅ Ви увійшли як {role.name.lower()}",
            parse_mode="html",
        )

        # Запускаем основное действие
        await action(db, callback.message, state, user, role, branch_id)

    @teacher_start_router.callback_query(F.data == "start")
    async def go_to_start(callback: CallbackQuery, state: FSMContext,
                          db: AsyncSession):
        await callback.answer()
        data = await state.get_data()

        user = await get_user_by_id(db, data["user_id"], with_roles=True)
        role = await get_role_by_id(db, data["role_id"])
        branch_id = data["branch_id"]

        await action(db, callback.message, state, user, role, branch_id)

    @teacher_start_router.callback_query(F.data == "back_to_select_role")
    async def back_to_select_role(callback: CallbackQuery,
                                  state: FSMContext,
                                  db: AsyncSession):
        hi_emoji = random.choice(emojis)
        data = await state.get_data()
        user = await get_user_by_id(db, data["user_id"], with_roles=True)
        await callback.message.delete()
        await callback.message.answer(
            text=f"{hi_emoji} Оберіть роль, під якою ви хочете увійти:",
            reply_markup=await Markup.select_role(user, user.roles)
        )


    return teacher_start_router
