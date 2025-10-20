from sqlalchemy import select

from app.Objects.TicketFlow.SettingsModel import TicketFlowSettings


class Settings:
    def __init__(self, db):
        self.db = db

    async def Get(self, branch_id: str):
        result = await self.db.execute(
            select(TicketFlowSettings).where(TicketFlowSettings.branch_id == branch_id)
        )
        return result.scalar_one_or_none()

    async def Update(self, branch_id: str, settings: dict):
        result = await self.db.execute(
            select(TicketFlowSettings).where(TicketFlowSettings.branch_id == branch_id)
        )
        db_settings = result.scalar_one_or_none()

        if db_settings:
            for key, value in settings.items():
                setattr(db_settings, key, value)
        else:
            db_settings = TicketFlowSettings(branch_id=branch_id, **settings)
            self.db.add(db_settings)

        await self.db.commit()
        await self.db.refresh(db_settings)
        return db_settings