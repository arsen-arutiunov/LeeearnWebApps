from fastapi import APIRouter

auth_router = APIRouter(prefix="/Auth", tags=["Auth"])

@auth_router.get("/Leeearn/Login")
async def auth_login():
    return {"message": "Hello World Login"}

@auth_router.get("/Leeearn/Callback")
async def auth_callback():
    return {"message": "Hello World Callback"}