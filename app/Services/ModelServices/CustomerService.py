from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from app.Objects.CustomerModel import Customer


async def get_customer_by_user_id(session: AsyncSession,
                                  user_id: UUID) -> Customer | None:
    result = await session.execute(
        select(Customer).where(Customer.user_id == user_id))
    return result.scalar_one_or_none()


async def get_customer_by_phone(session: AsyncSession,
                                phone: str) -> Customer | None:
    result = await session.execute(
        select(Customer).where(Customer.phone == phone))
    return result.scalar_one_or_none()


async def get_customer_by_leeearn_id(session: AsyncSession,
                                     leeearn_id: UUID) -> Customer | None:
    result = await session.execute(
        select(Customer).where(Customer.leeearn_id == leeearn_id))
    return result.scalar_one_or_none()


async def get_customer_by_email(session: AsyncSession,
                                email: str) -> Customer | None:
    result = await session.execute(
        select(Customer).where(Customer.email == email))
    return result.scalar_one_or_none()


async def get_all_customers(session: AsyncSession) -> Sequence[Customer]:
    result = await session.execute(select(Customer))
    return result.scalars().all()


async def create_customer(
        session: AsyncSession,
        user_id: UUID,
        leeearn_id: UUID | None = None,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None
) -> Customer:
    customer = Customer(
        user_id=user_id,
        leeearn_id=leeearn_id,
        name=name,
        email=email,
        phone=phone
    )
    session.add(customer)
    await session.commit()
    await session.refresh(customer)
    return customer


async def update_customer(
        session: AsyncSession,
        user_id: UUID,
        update_data: dict
) -> Customer | None:
    result = await session.execute(
        select(Customer).where(Customer.user_id == user_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return None

    for key, value in update_data.items():
        if hasattr(customer, key):
            setattr(customer, key, value)

    await session.commit()
    await session.refresh(customer)
    return customer


async def delete_customer(session: AsyncSession, user_id: UUID) -> bool:
    result = await session.execute(
        select(Customer).where(Customer.user_id == user_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return False

    await session.delete(customer)
    await session.commit()
    return True
