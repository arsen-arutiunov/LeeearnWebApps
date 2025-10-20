import uuid
from datetime import datetime, timedelta
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Objects.BranchModel import Branch
from app.Objects.PlanModel import Plan
from app.Objects.SubscriptionModel import Subscription, SubscriptionStatus


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 📦 Створити підписку
    async def CreateSubscription(
        self,
        branch_id: uuid.UUID,
        webapp_id: uuid.UUID,
        plan_id: uuid.UUID,
        auto_renew: bool = False
    ) -> Subscription:

        # ✅ Перевіримо існування гілки, вебаппу і плану
        branch = await self.db.get(Branch, branch_id)
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")

        webapp = await self.db.get(Webapp, webapp_id)
        if not webapp:
            raise HTTPException(status_code=404, detail="Webapp not found")

        plan = await self.db.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        # 🔁 Перевіримо, чи вже є активна підписка
        existing_sub = await self.db.execute(
            select(Subscription).where(
                Subscription.branch_id == branch_id,
                Subscription.webapp_id == webapp_id,
                Subscription.status == SubscriptionStatus.active
            )
        )
        if existing_sub.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Active subscription already exists for this branch and webapp"
            )

        # 🗓️ Створюємо нову підписку
        new_subscription = Subscription(
            branch_id=branch_id,
            webapp_id=webapp_id,
            plan_id=plan_id,
            active_until=datetime.utcnow() + timedelta(days=plan.duration_days),
            status=SubscriptionStatus.active,
            auto_renew=auto_renew
        )

        self.db.add(new_subscription)
        await self.db.commit()
        await self.db.refresh(new_subscription)
        return new_subscription

    # 🔍 Отримати підписку
    async def GetSubscription(self, subscription_id: uuid.UUID) -> type[Subscription]:
        subscription = await self.db.get(Subscription, subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return subscription

    # 📜 Отримати всі підписки для гілки
    async def GetSubscriptionsForBranch(self, branch_id: uuid.UUID) -> Sequence[Subscription]:
        result = await self.db.execute(
            select(Subscription).where(Subscription.branch_id == branch_id)
        )
        return result.scalars().all()

    # 🔁 Продовжити підписку (renew)
    async def RenewSubscription(self, subscription_id: uuid.UUID) -> type[Subscription]:
        subscription = await self.db.get(Subscription, subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        plan = await self.db.get(Plan, subscription.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        subscription.active_until += timedelta(days=plan.duration_days)
        subscription.status = SubscriptionStatus.active

        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    # ❌ Скасувати підписку
    async def CancelSubscription(self, subscription_id: uuid.UUID) -> type[Subscription]:
        subscription = await self.db.get(Subscription, subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription.status = SubscriptionStatus.cancelled
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    # 🧹 Автоматично позначити прострочені підписки
    async def MarkExpiredSubscription(self) -> int:
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.active_until < datetime.utcnow(),
                Subscription.status == SubscriptionStatus.active
            )
        )
        expired = result.scalars().all()
        for s in expired:
            s.status = SubscriptionStatus.expired
        await self.db.commit()
        return len(expired)
