import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
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

    class MoveLessonStates(StatesGroup):
        waiting_for_time = State()

    @teacher_router_lessons.callback_query(lambda c: c.data == "start_lessons")
    async def show_schedule(callback: CallbackQuery,
                            state: FSMContext,
                            db: AsyncSession):
        await callback.message.edit_caption(
            caption=await Text.lessons(),
            reply_markup=await Markup.lessons_menu(),
            parse_mode="html"
        )

    @teacher_router_lessons.callback_query(
        lambda c: c.data == "lesson_move_accept")
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
        now = datetime(2025, 10, 10, 16, 10, 0)
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
    async def lesson_move(callback: CallbackQuery, state: FSMContext,
                          db: AsyncSession):
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

    def parse_schedule_input(schedule_input):
        schedule = defaultdict(list)
        for entry in schedule_input:
            day = entry["day"]
            from_time = entry["from"][:5]
            to_time = entry["to"][:5]
            schedule[day].append((from_time, to_time))
        return schedule

    def get_upcoming_dates_with_slots(schedule_input, max_count=7):
        today = datetime.today().date()
        today = datetime(2025, 10, 10, 16, 10, 0).date()
        schedule = parse_schedule_input(schedule_input)
        result = []

        current_date = today
        while len(result) < max_count:
            weekday = current_date.weekday()
            if weekday in schedule:
                result.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "slots": schedule[weekday]
                })
            current_date += timedelta(days=1)

            # Stop early if пройшли всі доступні дні в розкладі (макс 14 днів вперед)
            if (
                    current_date - today).days > 30:  # failsafe: не зациклюватись вічно
                break

        return result

    def parse_datetime(dt_str: str) -> datetime:
        """Парсить дату з рядка у datetime."""
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")

    def remove_occupied_slots(slots_by_date: list[dict],
                              upcoming_lessons: list[dict]) -> list[dict]:
        updated_slots = []

        for day_entry in slots_by_date:
            date_str = day_entry["date"]
            slots = day_entry["slots"]
            date_obj = datetime.strptime(date_str,
                                         "%Y-%m-%d").date()  # <--- саме .date()

            # Залишаємо лише уроки цього дня, але з урахуванням +2 годин
            day_lessons = []
            for lesson in upcoming_lessons:
                lesson_start = parse_datetime(lesson["date"]) + timedelta(
                    hours=2)
                if lesson_start.date() == date_obj:
                    lesson_end_raw = parse_datetime(lesson["endDate"])
                    if lesson_end_raw.year == 1:
                        raise ValueError("Invalid endDate")
                    lesson_end = lesson_end_raw + timedelta(hours=2)

                    day_lessons.append((lesson_start, lesson_end,
                                        lesson))  # додали і lesson для тривалості

            for lesson_start, lesson_end, lesson in day_lessons:
                # Якщо немає endDate, fallback на minutesEstimated
                if not lesson_end:
                    minutes = lesson["lesson"].get("minutesEstimated", 30)
                    lesson_end = lesson_start + timedelta(minutes=minutes)

                new_slots = []
                for free_from, free_to in slots:
                    slot_start = datetime.combine(date_obj,
                                                  datetime.strptime(free_from,
                                                                    "%H:%M").time())
                    slot_end = datetime.combine(date_obj,
                                                datetime.strptime(free_to,
                                                                  "%H:%M").time())

                    # Якщо немає перетину — залишаємо як є
                    if lesson_end <= slot_start or lesson_start >= slot_end:
                        new_slots.append((free_from, free_to))
                    else:
                        # Відрізаємо заняту частину
                        if lesson_start > slot_start:
                            new_slots.append((slot_start.strftime("%H:%M"),
                                              lesson_start.strftime("%H:%M")))
                        if lesson_end < slot_end:
                            new_slots.append((lesson_end.strftime("%H:%M"),
                                              slot_end.strftime("%H:%M")))

                slots = new_slots

            updated_slots.append({
                "date": date_str,
                "slots": slots
            })

        return updated_slots

    @teacher_router_lessons.callback_query(F.data.startswith("choose_lesson:"))
    async def choose_lesson(callback: CallbackQuery, state: FSMContext,
                            db: AsyncSession):
        user = await get_user_by_telegram_id(db, callback.from_user.id,
                                             with_roles=True)
        lesson_id = callback.data.split(":")[1]
        await state.update_data(user_id=user.id, lesson_id=lesson_id)
        client = PlatformClient(
            PLATFORM_API_URL,
            MAIN_PLATFORMA_API_ID,
            MAIN_PLATFORMA_API_ACCESS_TOKEN
        )
        client.debug_logs = True
        branch = client.GetBranch(user.branch_id)

        lessons_items = await branch.Teachers.GetScheduleItemList(
            teacher_id=user.id
        )
        all_data = lessons_items.json()
        schedule_items = all_data.get('data', {}).get('data', [])
        schedule_item = None

        for item in schedule_items:
            if item.get("id") == lesson_id:
                schedule_item = item
                group_id = schedule_item.get('group').get('id')

            if schedule_item:
                break

        if not schedule_item:
            await callback.answer("❌ Уроку не знайдено.")

        today = datetime.utcnow().date()
        two_weeks_later = today + timedelta(weeks=2)

        response = await branch.GroupSchedule.GetTeachersSchedule(
            group_id=group_id,
            data={
                "from": today.strftime("%Y-%m-%d"),
                "to": two_weeks_later.strftime("%Y-%m-%d")
            }
        )
        teacher_work_days = response.json().get(
            "data").get("regularScheduleInputRequests").get("$values", None)
        if len(teacher_work_days) == 0:
            await callback.answer("❌ Не встановлений графік.")
            return

        teacher_dirty_slots = get_upcoming_dates_with_slots(teacher_work_days)
        cleaned_teacher_slots = remove_occupied_slots(teacher_dirty_slots,
                                                      schedule_items)

        await callback.message.edit_caption(
            caption="Оберіть дату на яку бажаєте перенести урок:",
            reply_markup=await Markup.lesson_date_move(cleaned_teacher_slots)
        )
        await state.update_data(group_id=group_id)

    @teacher_router_lessons.callback_query(F.data.startswith("date_move:"))
    async def choose_time_move_lesson(callback: CallbackQuery,
                                      state: FSMContext,
                                      db: AsyncSession):
        date_str = callback.data.split(":")[1]
        await state.update_data(selected_date=date_str)
        await callback.message.edit_caption(
            caption=f"Обрана дата: {date_str}\n\n"
                    f"Напишіть час у форматі ГГ:ХХ",
            reply_markup=None
        )

        await state.update_data(main_message_id=callback.message.message_id)

        await state.set_state(MoveLessonStates.waiting_for_time)

    @teacher_router_lessons.message(MoveLessonStates.waiting_for_time)
    async def handle_time_input(message: Message, state: FSMContext, db: AsyncSession):
        time_str = message.text.strip()
        message_id = message.message_id

        # Отримуємо збережену дату
        state_data = await state.get_data()
        selected_date = state_data.get("selected_date")
        main_message_id = state_data.get("main_message_id")

        if not selected_date:
            await message.answer("Помилка: дата не обрана.")
            return

        try:
            full_datetime = datetime.strptime(f"{selected_date} {time_str}",
                                              "%Y-%m-%d %H:%M")
        except ValueError:
            await message.answer(
                "Невірний формат часу. Введіть у форматі ГГ:ХХ")
            return

        user = await get_user_by_telegram_id(db, message.from_user.id,
                                             with_roles=True)
        client = PlatformClient(
            PLATFORM_API_URL,
            MAIN_PLATFORMA_API_ID,
            MAIN_PLATFORMA_API_ACCESS_TOKEN
        )
        client.debug_logs = True
        branch = client.GetBranch(user.branch_id)
        try:
            response = await branch.GroupSchedule.Move(
                group_id=state_data.get("group_id"),
                data={
                    "id": state_data.get("lesson_id"),
                    "date": f"{selected_date}T{time_str}:00.000Z",
                    "comment": "Перенесення уроку"
                }
            )

            await message.delete()
            await message.bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=main_message_id,
                caption=f"✅ Урок було перенесено на {full_datetime.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=await Markup.lessons_menu()
            )
        except Exception:
            await message.delete()
            await message.bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=main_message_id,
                caption=f"❌ При перенесенні урока виникла помилка.",
                reply_markup=await Markup.lessons_menu()
            )



    @teacher_router_lessons.callback_query(F.data.startswith("choose_date:"))
    async def choose_date(callback: CallbackQuery, state: FSMContext,
                          db: AsyncSession):
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
            caption=f"Дата: {start_date_str}\n\nОберіть урок:",
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
        now = datetime(2025, 10, 30, 16, 10, 0)

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

                    print(item)
                    return {
                        "group": item.get("group", None).get("id", None),
                        "lesson_id": item.get('id'),
                        'lesson_name': lesson_name,
                        'start_time': start_dt.strftime('%H:%M'),
                        'end_time': end_dt.strftime('%H:%M'),
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

    @teacher_router_lessons.callback_query(
        lambda c: c.data == "lesson_confirm_students")
    async def lesson_confirm_students(callback: CallbackQuery,
                                      state: FSMContext, db: AsyncSession):
        user = await get_user_by_telegram_id(db, callback.from_user.id,
                                             with_roles=True)
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

        client = PlatformClient(
            PLATFORM_API_URL,
            MAIN_PLATFORMA_API_ID,
            MAIN_PLATFORMA_API_ACCESS_TOKEN
        )
        client.debug_logs = True
        branch = client.GetBranch(user.branch_id)
        if lesson and lesson.get('group') and lesson.get('lesson_id'):
            lesson_students = (await branch.GroupSchedule.GetDetails(
                group_id=lesson.get('group'),
                data=lesson.get('lesson_id')
            )).json()
            students = []
            for student in lesson_students["data"]["studentList"]["$values"]:
                if student["managerConfirmed"] is False:
                    students.append({student["studentUser"]["displayName"]:
                                         student["studentUserId"]})

        text = (f"Підтвердження присутності учнів на уроці.\n\n"
                f"Урок:\n{lesson['lesson_name']} | "
                f"{lesson['start_time']} - {lesson['end_time']}")

        print(students)

        if not students:
            text += "\n\n Немає непідтверджених учнів."

        await callback.message.edit_caption(
            caption=text,
            reply_markup=await Markup.lesson_confirm_student_list(students)
        )
        return

    @teacher_router_lessons.callback_query(
        F.data.startswith("lesson_confirm_student:"))
    async def handle_student_confirm(callback: CallbackQuery,
                                     state: FSMContext,
                                     db: AsyncSession):
        user = await get_user_by_telegram_id(db, callback.from_user.id,
                                             with_roles=True)
        data = callback.data.split(":")[1]

        client = PlatformClient(
            PLATFORM_API_URL,
            MAIN_PLATFORMA_API_ID,
            MAIN_PLATFORMA_API_ACCESS_TOKEN
        )
        client.debug_logs = True
        branch = client.GetBranch(user.branch_id)

        lesson = await get_current_lesson(
            branch_id=user.branch_id,
            teacher_id=user.id,
        )

        response = await branch.GroupSchedule.ConfirmStudent(
            group_id=lesson.get('group'),
            data={
                "groupScheduleItemId": lesson.get('lesson_id'),
                "userId": data,
                "confirmed": True
            }
        )

        await callback.answer(f"✅ Учень був відмічений як присутній.",
                              show_alert=True)

        await callback.message.edit_caption(
            caption="Тут зібрали найчастіші запити до будь яких відділів.",
            reply_markup=await Markup.lessons_menu()
        )

    return teacher_router_lessons
