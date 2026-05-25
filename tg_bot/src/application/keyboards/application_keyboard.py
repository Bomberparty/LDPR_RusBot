from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.application.callbacks import AppViewCallback, SendApplicationCallback

def get_application_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Отправить текстовое обращение", callback_data=SendApplicationCallback(action="text").pack())
    kb.button(text="📷 Отсканировать фото обращения", callback_data=SendApplicationCallback(action="photo").pack())
    kb.adjust(1)
    return kb.as_markup()

def get_applications_list_keyboard(apps, page: int, total_count: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for app in apps:
        kb.button(
            text=f"📄 {app.sender_fio or 'Аноним'} -> {app.deputy_fio} | {app.created_at.strftime('%d.%m.%Y')}",
            callback_data="app_detail_dummy" # Можно расширить позже
        )
    kb.adjust(1)
    
    if total_count > 4:
        nav_kb = InlineKeyboardBuilder()
        if page > 0:
            nav_kb.button(text="⬅️ Назад", callback_data=AppViewCallback(page=page - 1).pack())
        if (page + 1) * 4 < total_count:
            nav_kb.button(text="➡️ Вперёд", callback_data=AppViewCallback(page=page + 1).pack())
        nav_kb.adjust(2)
        kb.attach(nav_kb)
        
    return kb.as_markup()
