import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from src.application.states import ApplicationPhotoStates
from src.application.callbacks import AppViewCallback, FieldSelectCallback
from src.application.keyboards.menu_keyboard import get_menu_keyboard
from src.application.keyboards.application_keyboard import (
    get_edit_menu_keyboard,
    get_field_suggestions_keyboard,
    get_applications_list_keyboard
)
from src.services.interfaces import IApplicationService
from src.domain.interfaces import IGeminiExtractor, IStringSorterRepository

router = Router(name=__name__)
logger = logging.getLogger(__name__)

FIELD_MAP = {
    "ФИО отправителя": "sender_fio",
    "Текст обращения": "application_text",
    "ФИО депутата": "deputy_fio"
}

FIELD_DISPLAY_NAMES = {v: k for k, v in FIELD_MAP.items()}

@router.message(F.text == "Сканировать обращение")
async def start_scan_application(message: types.Message, state: FSMContext):
    await state.set_state(ApplicationPhotoStates.waiting_photo)
    await message.answer(
        "📷 Пожалуйста, отправьте чёткое фото обращения. Поддерживаются форматы изображений."
    )


@router.message(ApplicationPhotoStates.waiting_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext, gemini_extractor: IGeminiExtractor):
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_bytes = (await message.bot.download_file(file_info.file_path)).read()

    await message.answer("🔄 Начинаю обработку фото нейросетью Gemini... Это может занять несколько секунд.")
    try:
        extracted = await gemini_extractor.extract_application_data(file_bytes)
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")
        await message.answer(
            "❌ Произошла ошибка при анализе изображения. Попробуйте отправить другое фото.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return

    await state.update_data(app_photo_data=extracted)
    await state.set_state(ApplicationPhotoStates.editing)

    text = (
        f"📄 *Распознанные данные обращения:*\n\n"
        f"👤 *ФИО отправителя:* {extracted['sender_fio']}\n"
        f"📝 *Текст обращения:* {extracted['application_text']}\n"
        f"🏛 *ФИО депутата:* {extracted['deputy_fio']}\n\n"
        f"Выберите действие: сохраните обращение или отредактируйте данные."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_edit_menu_keyboard())


@router.message(ApplicationPhotoStates.waiting_photo)
async def wrong_photo_type(message: types.Message):
    await message.reply("⚠️ Пожалуйста, отправьте именно фотографию или изображение документа (не видео, не файлы).")


@router.message(F.text == "✏️ Отредактировать", ApplicationPhotoStates.editing)
async def start_edit_field(message: types.Message, state: FSMContext):
    await state.set_state(ApplicationPhotoStates.typing_field)
    await message.reply("Начните вводить название поля для редактирования (например: ФИО отправителя, Текст обращения, ФИО депутата):")


@router.message(ApplicationPhotoStates.typing_field)
async def search_field(message: types.Message, state: FSMContext, string_sorter: IStringSorterRepository):
    user_input = message.text.strip()
    if not user_input:
        return await message.reply("Введите название поля.")

    all_fields = list(FIELD_MAP.keys())
    try:
        sorted_fields = await string_sorter.sort_by_similarity(user_input, all_fields)
        suggestions = sorted_fields[:3]
    except Exception:
        suggestions = [f for f in all_fields if user_input.lower() in f.lower()]

    if not suggestions:
        return await message.reply("Поле не найдено. Попробуйте ввести название заново или нажмите '✅ Сохранить обращение', чтобы завершить.")

    field_options = {FIELD_MAP[name]: name for name in suggestions}
    await state.update_data(field_options=field_options)
    await state.set_state(ApplicationPhotoStates.selecting_field)

    await message.reply("Выберите поле из списка:", reply_markup=get_field_suggestions_keyboard(field_options))


@router.callback_query(FieldSelectCallback.filter(), ApplicationPhotoStates.selecting_field)
async def select_field_callback(query: types.CallbackQuery, callback_data: FieldSelectCallback, state: FSMContext):
    field_key = callback_data.field_key
    field_name = FIELD_DISPLAY_NAMES.get(field_key, field_key) 

    await state.update_data(editing_field_key=field_key, editing_field_name=field_name)
    await state.set_state(ApplicationPhotoStates.entering_value)

    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.reply(f"✏️ Введите новое значение для поля *{field_name}*: ", parse_mode="Markdown")


@router.message(ApplicationPhotoStates.entering_value)
async def enter_new_value(message: types.Message, state: FSMContext):
    new_value = message.text.strip()
    if not new_value:
        return await message.reply("Значение не может быть пустым.")

    data = await state.get_data()
    app_data = data.get("app_photo_data", {})
    field_key = data.get("editing_field_key")
    field_name = data.get("editing_field_name")

    if field_key:
        app_data[field_key] = new_value
        await state.update_data(app_photo_data=app_data)

    await state.set_state(ApplicationPhotoStates.editing)

    text = (
        f"📄 *Обновлённые данные обращения:*\n\n"
        f"👤 *ФИО отправителя:* {app_data.get('sender_fio')}\n"
        f"📝 *Текст обращения:* {app_data.get('application_text')}\n"
        f"🏛 *ФИО депутата:* {app_data.get('deputy_fio')}\n\n"
        f"Выберите действие: сохраните обращение или отредактируйте данные."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_edit_menu_keyboard())


@router.message(F.text == "✅ Сохранить обращение", ApplicationPhotoStates.editing)
async def save_photo_application(message: types.Message, state: FSMContext, app_service: IApplicationService, log_chat: str):
    data = await state.get_data()
    app_data = data.get("app_photo_data")
    
    if not app_data:
        return await message.reply("❌ Ошибка: данные обращения не найдены. Начните заново.", reply_markup=ReplyKeyboardRemove())

    try:
        app = await app_service.create_application(
            user_id=message.from_user.id,
            sender_fio=app_data.get("sender_fio"),
            deputy_fio=app_data.get("deputy_fio"),
            text=app_data.get("application_text")
        )
        
        log_msg = (
            f"📩 Новое обращение (ФОТО) от пользователя  "
            f"{'@' + message.from_user.username if message.from_user.username else 'ID:' + str(message.from_user.id)}\n"
            f"Отправитель: {app.sender_fio}\n"
            f"Депутат: {app.deputy_fio}\n"
            f"Текст:\n{app.application_text}\n"
            f"Дата: {app.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"ID: {app.id}"
        )
        await message.bot.send_message(chat_id=log_chat, text=log_msg)
        
        await message.answer(
            "✅ Ваше обращение успешно зарегистрировано и отправлено.", 
            reply_markup=get_menu_keyboard(has_applications=True)
        )
    except Exception as e:
        logger.error(f"Error saving photo application: {e}")
        await message.answer("Произошла ошибка при сохранении обращения в базе данных. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()


@router.message(F.text == "Мои обращения")
async def view_my_apps(message: types.Message, app_service: IApplicationService):
    apps, count = await app_service.get_user_applications(message.from_user.id, page=0)
    if not apps:
        return await message.answer("У вас пока нет обращений.")
    await message.answer(
        f"📂 Ваши обращения (всего: {count}):",
        reply_markup=get_applications_list_keyboard(apps, page=0, total_count=count)
    )


@router.callback_query(AppViewCallback.filter())
async def paginate_apps(query: types.CallbackQuery, callback_data: AppViewCallback, app_service: IApplicationService):
    apps, count = await app_service.get_user_applications(query.from_user.id, page=callback_data.page)
    await query.message.edit_reply_markup(reply_markup=get_applications_list_keyboard(apps, callback_data.page, count))