from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.Objects.BranchRoleModel import BranchRole
from app.Objects.UserModel import User


async def create_user(
        session: AsyncSession,
        telegram_id: int,
        name: str,
        branch_id: UUID
) -> User | None:
    """
    Создать пользователя (упрощенная версия без исключений).
    Возвращает None если пользователь уже существует.
    """
    existing_user = await get_user_by_telegram_id(session, telegram_id)
    if existing_user:
        return None

    new_user = User(
        telegram_id=telegram_id,
        name=name,
        branch_id=branch_id
    )

    session.add(new_user)

    try:
        await session.commit()
        await session.refresh(new_user)
        return new_user
    except IntegrityError:
        await session.rollback()
        return None


# ---- Получение ----

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int, with_roles: bool = False) -> User | None:
    """Получить пользователя по Telegram ID"""
    query = select(User).where(User.telegram_id == telegram_id)

    if with_roles:
        query = query.options(selectinload(User.roles))

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID, with_roles: bool = False) -> User | None:
    """Получить пользователя по user_id"""
    query = select(User).where(User.id == user_id)

    if with_roles:
        query = query.options(selectinload(User.roles))

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_roles(session: AsyncSession, user_id: UUID) -> list[BranchRole]:
    """Получить все роли пользователя"""
    user = await get_user_by_id(session, user_id, with_roles=True)
    if not user:
        return []
    return user.roles


# ---- Модификация ----

async def add_role_to_user(session: AsyncSession, user_id: UUID, role_id: UUID):
    """Добавить роль пользователю"""
    user = await get_user_by_id(session, user_id, with_roles=True)
    role = await session.get(BranchRole, role_id)
    if not user or not role:
        return None

    if role not in user.roles:
        user.roles.append(role)
        await session.commit()
        await session.refresh(user)

    return user


async def remove_role_from_user(session: AsyncSession, user_id: UUID, role_id: UUID):
    """Удалить роль у пользователя"""
    user = await get_user_by_id(session, user_id, with_roles=True)
    role = await session.get(BranchRole, role_id)
    if not user or not role:
        return None

    if role in user.roles:
        user.roles.remove(role)
        await session.commit()
        await session.refresh(user)

    return user
