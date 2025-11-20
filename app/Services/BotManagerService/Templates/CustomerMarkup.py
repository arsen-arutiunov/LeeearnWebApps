import uuid

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.Objects.BranchRoleModel import BranchRole


class CustomerMarkup:
    @staticmethod
    def from_template(buttons_template: list[list[str]], row_width: int = 1) -> InlineKeyboardMarkup:
        """
        Створює клавіатуру на основі переданого шаблону кнопок.

        :param buttons_template: Список кнопок у форматі [[text, callback_data], ...].
        :param row_width: Кількість кнопок в одному рядку.
        :return: InlineKeyboardMarkup
        """
        kb = InlineKeyboardBuilder()

        for button in buttons_template:
            if len(button) == 2:  # Очікуємо формат ["text", "callback_data"]
                if "https" in button[1]:
                    kb.button(text=button[0], url=button[1])
                else:
                    kb.button(text=button[0], callback_data=button[1])

        kb.adjust(row_width)  # Розташування кнопок по рядках

        return kb.as_markup()

    @staticmethod
    async def customer_menu():
        buttons = [
            ["Посилання на урок", "lesson_link"],
            ["Немає уроку", "forwarding_no_lesson"],
            ["Мій баланс", "my_balance"],
            # ["Змінити розклад", "forwarding_change_schedule"],
            ["Перенести урок", "reschedule_lesson"],
            # ["Змінити викладача", "change_teacher"],
            # ["Хочу ще один предмет", "add_subject"],
            # ["Абонемент", "subscription"],
            # ["Реквізити", "start_requisites"],
            ["Подзвоніть мені", "forwarding_call_me"],
            ["Соціальні мережі", "social_networks"],
            ["Змінити роль ↩️", "back_to_select_role"]
        ]
        return CustomerMarkup.from_template(buttons, row_width=2)

    @staticmethod
    async def social_networks_menu(social_networks: dict):
        buttons = [
            [InlineKeyboardButton(text=social_media, url=link)] for
            social_media, link in social_networks.items()
        ]
        buttons.append(
            [InlineKeyboardButton(text="Повернутись ↩️",
                                  callback_data="start")]
        )
        return types.InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    async def back_to_customers_menu():
        buttons = [
            ["Повернутись ↩️", "start"]
        ]
        return CustomerMarkup.from_template(buttons, row_width=1)

    @staticmethod
    async def forwarding_no_lesson_menu(lesson: dict):
        buttons = [
            ["Підтвердити", f"no_lesson:{lesson['lesson_id']}"],
            ["Повернутись ↩️", "start"]
        ]
        return CustomerMarkup.from_template(buttons, row_width=2)

    @staticmethod
    async def forwarding_call_me(user_id: uuid.UUID):
        buttons = [
            ["Підтвердити", f"call_me_confirm:{user_id}"],
            ["Повернутись ↩️", "start"]
        ]
        return CustomerMarkup.from_template(buttons, row_width=2)
