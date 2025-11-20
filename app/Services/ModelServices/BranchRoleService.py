from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.Objects.BranchRoleModel import BranchRole
from app.Objects.UserModel import User


# ---- Получение ----

async def get_role_by_id(session: AsyncSession, role_id: UUID) -> BranchRole | None:
    """Получить роль по ID"""
    result = await session.execute(select(BranchRole).where(BranchRole.id == role_id))
    return result.scalar_one_or_none()


async def get_all_roles(session: AsyncSession) -> Sequence[BranchRole]:
    """Получить все роли"""
    result = await session.execute(select(BranchRole))
    return result.scalars().all()


async def get_role_users(session: AsyncSession, role_id: UUID) -> list[User]:
    """Получить всех пользователей роли"""
    role = await get_role_by_id(session, role_id)
    if not role:
        return []
    return role.users


# ---- Модификация ----

async def create_role(session: AsyncSession, name: str, branch_id: UUID) -> BranchRole:
    """Создать новую роль"""
    role = BranchRole(name=name, branch_id=branch_id)
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


async def delete_role(session: AsyncSession, role_id: UUID) -> bool:
    """Удалить роль по ID"""
    role = await get_role_by_id(session, role_id)
    if not role:
        return False

    await session.delete(role)
    await session.commit()
    return True


async def add_user_to_role(session: AsyncSession, role_id: UUID, user_id: UUID):
    """Добавить пользователя в роль"""
    role = await get_role_by_id(session, role_id)
    user = await session.get(User, user_id)
    if not role or not user:
        return None

    if user not in role.users:
        role.users.append(user)
        await session.commit()
        await session.refresh(role)

    return role


async def remove_user_from_role(session: AsyncSession, role_id: UUID, user_id: UUID):
    """Удалить пользователя из роли"""
    role = await get_role_by_id(session, role_id)
    user = await session.get(User, user_id)
    if not role or not user:
        return None

    if user in role.users:
        role.users.remove(user)
        await session.commit()
        await session.refresh(role)

    return role