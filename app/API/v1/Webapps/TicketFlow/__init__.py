from fastapi import APIRouter

ticket_flow_router = APIRouter(prefix="/TicketFlow")

@ticket_flow_router.get("/GetHealth")
async def ping(branch_id: str):
    return {"message": f"Stability '{branch_id}'"}