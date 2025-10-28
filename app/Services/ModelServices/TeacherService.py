from typing import Any, Coroutine, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.Objects.TeacherModel import Teacher


# ---- Получение ----

async def get_teacher_by_user_id(session: AsyncSession,
                                 user_id: UUID) -> Teacher | None:
    """Получить преподавателя по user_id"""
    result = await session.execute(
        select(Teacher).where(Teacher.user_id == user_id))
    return result.scalar_one_or_none()


async def get_all_teachers(session: AsyncSession) -> Sequence[Teacher]:
    """Получить всех преподавателей"""
    result = await session.execute(select(Teacher))
    return result.scalars().all()


# ---- Создание ----

async def create_teacher(
        session: AsyncSession,
        user_id: UUID,
        leeearn_id: UUID,
        additional_branch_id: int = 0,
        is_contract_accepted: bool = False,
        contract_accepted_time: str | None = None,
        guide_message_id: int | None = None,
        weekly_points: int = 0,
        monthly_points: int = 0,
        setting_delete_proofs: bool = True,
        setting_report_notification: bool = True,
        setting_time_zone: str | None = None,
        setting_screenshot_time_kyiv: bool = False
) -> Teacher:
    """Создать запись преподавателя"""
    teacher = Teacher(
        user_id=user_id,
        leeearn_id=leeearn_id,
        additional_branch_id=additional_branch_id,
        is_contract_accepted=is_contract_accepted,
        contract_accepted_time=contract_accepted_time,
        guide_message_id=guide_message_id,
        weekly_points=weekly_points,
        monthly_points=monthly_points,
        setting_delete_proofs=setting_delete_proofs,
        setting_report_notification=setting_report_notification,
        setting_time_zone=setting_time_zone,
        setting_screenshot_time_kyiv=setting_screenshot_time_kyiv
    )
    session.add(teacher)
    await session.commit()
    await session.refresh(teacher)
    return teacher


# ---- Обновление ----

async def update_teacher(
        session: AsyncSession,
        user_id: UUID,
        **kwargs
) -> Teacher | None:
    """Обновить данные преподавателя"""
    result = await session.execute(
        select(Teacher).where(Teacher.user_id == user_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        return None

    for key, value in kwargs.items():
        if hasattr(teacher, key):
            setattr(teacher, key, value)

    await session.commit()
    await session.refresh(teacher)
    return teacher


# ---- Удаление ----

async def delete_teacher(session: AsyncSession, user_id: UUID) -> bool:
    """Удалить преподавателя"""
    teacher = await get_teacher_by_user_id(session, user_id)
    if not teacher:
        return False

    await session.delete(teacher)
    await session.commit()
    return True


# ---- Проверка ----

async def is_teacher_exists(session: AsyncSession, user_id: UUID) -> bool:
    """Проверить, существует ли преподаватель"""
    result = await session.execute(
        select(Teacher).where(Teacher.user_id == user_id))
    return result.scalar_one_or_none() is not None
