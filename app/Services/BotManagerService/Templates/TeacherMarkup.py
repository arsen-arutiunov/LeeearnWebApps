from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.Objects.BranchRoleModel import BranchRole
from app.Objects.UserModel import User


class TeacherMarkup:
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
    async def select_role(user: User, roles: list[BranchRole]):
        buttons = []
        for role in roles:
            buttons.append([role.name, f"select_role:{role.id}"])
        return TeacherMarkup.from_template(buttons, row_width=1)


    @staticmethod
    async def teacher_menu():
        buttons = [
            ["Мій розклад на сьогодні", "start_schedule"],
            ["Керування уроками", "start_lessons"],
            # ["Подивитися свій рейтинг", "my_rating"],
            ["Загальна допомога", "start_help"],
            # ["Налаштування", "start_settings"],
            ["Змінити роль ↩️", "back_to_select_role"]
        ]
        return TeacherMarkup.from_template(buttons, row_width=1)

    @staticmethod
    async def start_help(supervisor_url, branch):
        buttons = [
            # ["Мій рейтинг", "rating"],
            # ["Взяти вихідний", "dayoff"],
            ["Буде посилання на тг",
             "https://t.me/example"],
            ["Буде посилання на сайт",
             f"https://example.com"],
            ["Повернутись ↩️", "start"]
        ]
        return TeacherMarkup.from_template(buttons, row_width=2)

    @staticmethod
    async def curators_menu():
        buttons = [
            ["Змінити роль ↩️", "back_to_select_role"]
        ]
        return TeacherMarkup.from_template(buttons, row_width=1)

    @staticmethod
    async def lessons_menu():
        buttons = [
            ["Відмітити присутність учнів", "lesson_confirm_students"],
            ["Перенести плановий урок", "lesson_move_accept"],
            ["Зробити звіт за урок", "lesson_report"],
            ["Повернутись ↩️", "start"]
        ]
        return TeacherMarkup.from_template(buttons, row_width=1)

    @staticmethod
    async def schedule_menu():
        buttons = [
            ["📅 Сьогодні", "start_schedule"],
            ["📆 Завтра", "start_schedule_tomorrow"],
            ["🔁 Оновити", "start_schedule"],
            ["Повернутись ↩️", "start"]
        ]
        return TeacherMarkup.from_template(buttons, row_width=2)

    @staticmethod
    async def move_lesson_acceptation():
        buttons = [
            ["Продовжити", "lesson_move"],
            ["Повернутись ↩️", "start_lessons"]
        ]
        return TeacherMarkup.from_template(buttons, row_width=2)

    @staticmethod
    async def lesson_confirm_student_list(students):
        buttons = []
        for student in students:
            for name, lesson_id in student.items():
                buttons.append(
                    [name, f"lesson_confirm_student:{lesson_id}"]
                )
        buttons.append(["Повернутись ↩️", "start_lessons"])
        return TeacherMarkup.from_template(buttons, row_width=1)

    @staticmethod
    async def lesson_date_move(dates):
        buttons = []
        for date in dates:
            buttons.append([date['date'], f"date_move:{date['date']}"])
        buttons.append(["Повернутись ↩️", "start_lessons"])
        return TeacherMarkup.from_template(buttons, row_width=1)

    @staticmethod
    async def choose_lesson(lessons):
        buttons = []
        for lesson in lessons:
            buttons.append(
                [f"{lesson['lesson_name']} | "
                 f"{lesson['start_time'].split()[1]} - "
                 f"{lesson['end_time'].split()[1]}",
                 f"choose_lesson:{lesson['lesson_id']}"]
            )
        buttons.append(["Повернутись ↩️", "start_lessons"])
        return TeacherMarkup.from_template(buttons, row_width=1)

    @staticmethod
    async def choose_date(dates):
        buttons = []
        for date in dates:
            buttons.append(
                [f"{date}",
                 f"choose_date:{date}"])
        buttons.append(["Повернутись ↩️", "start_lessons"])
        return TeacherMarkup.from_template(buttons, row_width=1)
