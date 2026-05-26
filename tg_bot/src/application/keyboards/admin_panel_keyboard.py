from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.application.callbacks import AdminPanelCallback

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Повысить до Сотрудника", callback_data=AdminPanelCallback(action="promote_staff").pack())
    kb.adjust(1)
    return kb.as_markup()