from aiogram import Router

from app.Services.BotManagerService.Handlers.HelpHandler import (
    create_teacher_router_help
)
from app.Services.BotManagerService.Handlers.LessonsHandler import (
    create_teacher_router_lessons
)
from app.Services.BotManagerService.Handlers.ScheduleHandler import (
    create_teacher_router_schedule
)
from app.Services.BotManagerService.Handlers.StartHandler import (
    create_teacher_start_router
)

def create_main_router() -> Router:
    router = Router()
    router.include_router(create_teacher_start_router())
    router.include_router(create_teacher_router_help())
    router.include_router(create_teacher_router_lessons())
    router.include_router(create_teacher_router_schedule())
    return router
