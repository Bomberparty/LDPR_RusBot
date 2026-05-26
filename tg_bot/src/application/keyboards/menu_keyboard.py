from aiogram.utils.keyboard import ReplyKeyboardMarkup, ReplyKeyboardBuilder


def get_menu_keyboard(has_applications: bool = False) -> ReplyKeyboardMarkup:
    keyword = ReplyKeyboardBuilder()
    keyword.button(text="Загрузить видео")
    
    if has_applications:
        keyword.button(text="Мои обращения")
        
    keyword.button(text="Сканировать обращение")
    return keyword.as_markup(resize_keyboard=True)