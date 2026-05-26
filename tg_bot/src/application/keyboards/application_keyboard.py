from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from src.application.callbacks import AppViewCallback, FieldSelectCallback


def get_applications_list_keyboard(apps, page: int, total_count: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for app in apps:
        # Формируем кнопку на основе доступных полей модели Application
        kb.button(
            text=f"📄 Заявка №{app.id} | {app.created_at.strftime('%d.%m.%Y')}",
            callback_data="app_detail_dummy"
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


def get_edit_menu_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ Сохранить обращение")
    kb.button(text="✏️ Отредактировать")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def get_field_suggestions_keyboard(field_options: dict[str, str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, name in field_options.items():
        kb.button(text=name, callback_data=FieldSelectCallback(field_key=key).pack())
    kb.adjust(1)
    return kb.as_markup()