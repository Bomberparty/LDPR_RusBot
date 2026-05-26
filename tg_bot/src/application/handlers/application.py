import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from src.application.states import ApplicationStates, ApplicationPhotoStates
from src.application.callbacks import SendApplicationCallback, AppViewCallback, EditFieldCallback
from src.application.keyboards.menu_keyboard import get_menu_keyboard
from src.application.keyboards.application_keyboard import (
    get_application_main_keyboard,
    get_applications_list_keyboard,
    get_edit_fields_keyboard,
    get_save_photo_keyboard
)
from src.services.interfaces import IApplicationService
from src.domain.interfaces import IGeminiExtractor

router = Router(name=__name__)
logger = logging.getLogger(__name__)

# ==============================================================================
# ГЛАВНОЕ МЕНЮ ОБРАЩЕНИЙ
# ==============================================================================
@router.message(F.text == "Отправить обращение")
async def open_app_menu(message: types.Message):
    await message.answer(
        "Выберите способ отправки обращения:",
        reply_markup=get_application_main_keyboard()
    )

@router.callback_query(SendApplicationCallback.filter())
async def process_app_menu_callback(query: types.CallbackQuery, callback_data: SendApplicationCallback, state: FSMContext):
    await query.message.edit_text(f"Выбрано действие: {callback_data.action}")
    
    if callback_data.action == "photo":
        await query.message.answer("📷 Пожалуйста, отправьте чёткое фото обращения. Поддерживаются форматы изображений.")
        await state.set_state(ApplicationPhotoStates.waiting_photo)
        return
        
    if callback_data.action == "text":
        await query.message.answer("Укажите ФИО отправителя.\nЕсли хотите отправить от своего имени, отправьте `-` или `нет`.")
        await state.set_state(ApplicationStates.sender_fio)
        return
        
    await query.message.answer("Неизвестный вариант.")

# ==============================================================================
# ТЕКСТОВЫЙ РЕЖИМ (ОРИГИНАЛЬНАЯ ЛОГИКА)
# ==============================================================================
@router.message(ApplicationStates.sender_fio)
async def get_sender_fio(message: types.Message, state: FSMContext):
    fio = message.text.strip()
    if fio.lower() in ['-', 'нет', 'нету']:
        fio = None
    await state.update_data(sender_fio=fio)
    await message.answer("Введите текст обращения:")
    await state.set_state(ApplicationStates.text)

@router.message(ApplicationStates.text)
async def get_app_text(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("Текст обращения не может быть пустым.")
        return
    await state.update_data(application_text=text)
    await message.answer("Укажите ФИО депутата, на которого составляется обращение:")
    await state.set_state(ApplicationStates.deputy_fio)

@router.message(ApplicationStates.deputy_fio)
async def get_deputy_fio(message: types.Message, state: FSMContext, app_service: IApplicationService, log_chat: str):
    deputy = message.text.strip()
    if len(deputy) < 2:
        await message.answer("ФИО депутата должно содержать минимум 2 символа.")
        return

    data = await state.get_data()
    try:
        app = await app_service.create_application(
            user_id=message.from_user.id,
            sender_fio=data.get('sender_fio'),
            deputy_fio=deputy,
            text=data['application_text']
        )
        
        log_msg = (
            f"📩 Новое обращение от пользователя "
            f"{'@' + message.from_user.username if message.from_user.username else 'ID:' + str(message.from_user.id)}\n"
            f"Отправитель: {app.sender_fio or 'Используется ФИО из профиля'}\n"
            f"Депутат: {app.deputy_fio}\n"
            f"Текст:\n{app.application_text}\n"
            f"Дата: {app.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"ID обращения: {app.id}"
        )
        await message.bot.send_message(chat_id=log_chat, text=log_msg)
        
        await message.answer("✅ Ваше обращение успешно зарегистрировано и отправлено.", reply_markup=get_menu_keyboard(has_applications=True))
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        await message.answer("Произошла ошибка при сохранении обращения. Попробуйте позже.")

# ==============================================================================
# ФОТО РЕЖИМ (НОВАЯ ЛОГИКА С GEMINI)
# ==============================================================================
@router.message(ApplicationPhotoStates.waiting_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext, gemini_extractor: IGeminiExtractor):
    # Берем фото с максимальным разрешением
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_bytes = (await message.bot.download_file(file_info.file_path)).read()

    await message.answer("🔄 Начинаю обработку фото нейросетью Gemini... Это может занять несколько секунд.")
    try:
        extracted = await gemini_extractor.extract_application_data(file_bytes)
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")
        await message.answer("❌ Произошла ошибка при анализе изображения. Попробуйте отправить другое фото или используйте текстовый режим.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    await state.update_data(app_photo_data=extracted, editing_field=None)
    await state.set_state(ApplicationPhotoStates.editing)

    text = (
        f"📄 *Распознанные данные обращения:*\n\n"
        f"👤 *ФИО отправителя:* {extracted['sender_fio']}\n"
        f"📝 *Текст обращения:* {extracted['application_text']}\n"
        f"🏛 *ФИО депутата:* {extracted['deputy_fio']}\n\n"
        f"Выберите поле для редактирования или нажмите 'Сохранить', чтобы отправить."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_edit_fields_keyboard())
    await message.answer("Нажмите кнопку ниже, чтобы подтвердить данные:", reply_markup=get_save_photo_keyboard())

@router.message(ApplicationPhotoStates.waiting_photo)
async def wrong_photo_type(message: types.Message):
    await message.reply("⚠️ Пожалуйста, отправьте именно фотографию или изображение документа (не видео, не файлы).")

# --- Цикл редактирования распознанных полей ---
@router.callback_query(EditFieldCallback.filter(), ApplicationPhotoStates.editing)
async def edit_field_callback(query: types.CallbackQuery, callback_data: EditFieldCallback, state: FSMContext):
    field_name = callback_data.field
    field_label = {
        "sender_fio": "ФИО отправителя",
        "application_text": "Текст обращения",
        "deputy_fio": "ФИО депутата"
    }.get(field_name, "поле")
    
    await query.message.answer(f"✏️ Введите новое значение для поля *{field_label}*:", parse_mode="Markdown")
    await state.update_data(editing_field=field_name)

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
            f"📩 Новое обращение (ФОТО) от пользователя "
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

@router.message(ApplicationPhotoStates.editing, F.text != "✅ Сохранить обращение")
async def handle_edit_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("editing_field")
    
    if not field:
        return await message.reply("⚠️ Сначала выберите поле для изменения, нажав на соответствующую кнопку выше.")
        
    value = message.text.strip()
    if not value:
        return await message.reply("Значение не может быть пустым.")

    app_data = data.get("app_photo_data", {})
    app_data[field] = value
    await state.update_data(app_photo_data=app_data, editing_field=None)

    await message.answer(f"✅ Поле '{field}' успешно обновлено.", reply_markup=get_edit_fields_keyboard())
    await message.answer("Выберите другое поле или нажмите 'Сохранить', чтобы завершить:", reply_markup=get_save_photo_keyboard())

# ==============================================================================
# ПРОСМОТР ОБРАЩЕНИЙ (ОРИГИНАЛ)
# ==============================================================================
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