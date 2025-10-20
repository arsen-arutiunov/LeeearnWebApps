from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.Infrastructure.Database import getdb
from app.Services.Webapps.TicketFlow import TicketFlow

settings_router = APIRouter(prefix="/TicketFlow", tags=["TicketFlow"])

@settings_router.get("/Get")
async def get_settings(branch_id: str, db: AsyncSession = Depends(getdb)):
    return await TicketFlow(db).Settings.Get(branch_id)

@settings_router.post("/Update")
async def update_settings(
    branch_id: str,
    settings: dict = Body(...),
    db: AsyncSession = Depends(getdb)
):
    return await TicketFlow(db).Settings.Update(branch_id, settings)
