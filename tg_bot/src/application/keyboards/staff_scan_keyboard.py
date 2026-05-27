from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from src.application.callbacks import StaffScanTypeCallback, StaffFieldSelectCallback, StaffPdCallback


def get_scan_type_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📄 Сканировать своё обращение", callback_data=StaffScanTypeCallback(action="my").pack())
    kb.button(text="👤 Сканировать обращение другого человека", callback_data=StaffScanTypeCallback(action="other").pack())
    kb.adjust(1)
    return kb.as_markup()


def get_staff_edit_menu_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ Сохранить обращение")
    kb.button(text="✅ Сохранить и перейти к ПДн")
    kb.button(text="✏️ Отредактировать данные")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def get_staff_field_suggestions_keyboard(field_options: dict[str, str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, name in field_options.items():
        kb.button(text=name, callback_data=StaffFieldSelectCallback(field_key=key).pack())
    kb.adjust(1)
    return kb.as_markup()


def get_pd_upload_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="📄 Загрузить согласие ПДн")
    kb.button(text="⛔ Не загружать ПДн")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)