from fastapi import APIRouter

webapps_router = APIRouter(prefix="/Webapp/{branch_id}")

from .TicketFlow import ticket_flow_router
webapps_router.include_router(ticket_flow_router)