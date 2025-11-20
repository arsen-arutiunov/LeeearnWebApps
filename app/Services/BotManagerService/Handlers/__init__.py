from aiogram import Router

from app.Services.BotManagerService.Handlers.CustomerHandlers.MenuHandler import \
    customer_menu_handler
from app.Services.BotManagerService.Handlers.TeacherHandlers.HelpHandler import (
    create_teacher_router_help
)
from app.Services.BotManagerService.Handlers.TeacherHandlers.LessonsHandler import (
    create_teacher_router_lessons
)
from app.Services.BotManagerService.Handlers.TeacherHandlers.ScheduleHandler import (
    create_teacher_router_schedule
)
from app.Services.BotManagerService.Handlers.TeacherHandlers.StartHandler import (
    create_teacher_start_router
)

def create_main_router() -> Router:
    router = Router()
    router.include_router(create_teacher_start_router())
    router.include_router(create_teacher_router_help())
    router.include_router(create_teacher_router_lessons())
    router.include_router(create_teacher_router_schedule())
    router.include_router(customer_menu_handler())
    return router
