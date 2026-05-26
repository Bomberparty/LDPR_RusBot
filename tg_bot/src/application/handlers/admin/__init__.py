from aiogram import Router

from src.application.filters import AdminFilter
from .post import router as post_router
from .panel import router as panel_router

router = Router()
router.message.filter(AdminFilter())
router.include_router(post_router)
router.include_router(panel_router)