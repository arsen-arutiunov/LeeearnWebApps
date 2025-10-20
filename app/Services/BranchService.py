import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException, status

from app.Objects.BranchModel import Branch


class BranchService:
    def __init__(self, db_instance: AsyncSession):
        self.db = db_instance

    # 📦 Створити нову філію
    async def CreateBranch(
        self,
        id: uuid.UUID,
        title: str,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ) -> Branch:
        new_branch = Branch(
            id=id,
            title=title,
            icon=icon,
            color=color,
        )

        self.db.add(new_branch)
        await self.db.commit()
        await self.db.refresh(new_branch)

        return new_branch

    # 🔍 Отримати філію за ID
    async def GetBranch(self, branch_id: uuid.UUID) -> Branch:
        result = await self.db.execute(
            select(Branch).where(Branch.id == branch_id)
        )

        branch = result.scalar_one_or_none()

        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )

        return branch

    async def UpdateBranch(
        self,
        branch_id: uuid.UUID,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ) -> Branch:
        result = await self.db.execute(
            select(Branch).where(Branch.id == branch_id)
        )
        branch = result.scalar_one_or_none()
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )

        if title is not None:
            branch.title = title
        if icon is not None:
            branch.icon = icon
        if color is not None:
            branch.color = color

        await self.db.commit()
        await self.db.refresh(branch)

        return branch