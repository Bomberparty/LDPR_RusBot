import logging
from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from src.application.states import ApplicationPhotoStates, StaffApplicationStates
from src.application.callbacks import StaffScanTypeCallback, StaffFieldSelectCallback, StaffPdCallback
from src.application.keyboards.staff_scan_keyboard import (
    get_scan_type_keyboard, 
    get_staff_edit_menu_keyboard,
    get_staff_field_suggestions_keyboard, 
    get_pd_upload_keyboard,
)
from src.application.keyboards.menu_keyboard import get_menu_keyboard
from src.services.interfaces import IStaffApplicationService
from src.domain.interfaces import IGeminiExtractor, IStringSorterRepository

router = Router(name=__name__)
logger = logging.getLogger(__name__)

STAFF_FIELD_MAP = {
    "Фамилия": "surname",
    "Имя": "name",
    "Отчество": "patronymic",
    "Регион": "region",
    "Город": "city",
    "Домашний адрес": "home_address",
    "Дата рождения": "birth_date",
    "Телефон": "phone_number",
    "Почта": "email",
    "Текст обращения": "application_text",
    "Дата из документа": "obtained_data_at"
}
STAFF_FIELD_DISPLAY = {v: k for k, v in STAFF_FIELD_MAP.items()}

@router.callback_query(StaffScanTypeCallback.filter(), StaffApplicationStates.choice_type)
async def choose_scan_type(query: types.CallbackQuery, callback_data: StaffScanTypeCallback, state: FSMContext):
    await query.message.edit_reply_markup(reply_markup=None)
    if callback_data.action == "my":
        await state.clear()
        await state.set_state(ApplicationPhotoStates.waiting_photo)
        return await query.message.answer("📷 Пожалуйста, отправьте чёткое фото обращения...")
    
    await state.set_state(StaffApplicationStates.waiting_photo_other)
    await query.message.answer("📷 Пожалуйста, отправьте чёткое фото обращения другого человека...")

@router.message(StaffApplicationStates.waiting_photo_other, F.photo)
async def process_staff_photo(message: types.Message, state: FSMContext, gemini_extractor: IGeminiExtractor):
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_bytes = (await message.bot.download_file(file_info.file_path)).read()

    await message.answer("🔄 Начинаю обработку фото... Это может занять несколько секунд.")
    try:
        extracted = await gemini_extractor.extract_staff_application_data(file_bytes)
    except Exception as e:
        logger.error(f"Staff Gemini extraction failed: {e}")
        return await message.answer("❌ Ошибка анализа фото нейросетью. Попробуйте отправить другое изображение.", reply_markup=ReplyKeyboardRemove())

    extracted["file_id"] = photo.file_id
    await state.update_data(staff_app_data=extracted)
    await state.set_state(StaffApplicationStates.editing_other)

    text = "📄 *Распознанные данные:*\n\n"
    for k, v in STAFF_FIELD_MAP.items():
        text += f"{k}: {extracted.get(v, '-')}\n"
    text += "\nВыберите действие:"
    await message.answer(text, parse_mode="Markdown", reply_markup=get_staff_edit_menu_keyboard())

@router.message(F.text == "✏️ Отредактировать данные", StaffApplicationStates.editing_other)
async def start_staff_edit(message: types.Message, state: FSMContext):
    await state.set_state(StaffApplicationStates.typing_field_other)   
    await message.reply("Начните вводить название поля для редактирования:", reply_markup=ReplyKeyboardRemove())

@router.message(StaffApplicationStates.typing_field_other)
async def search_staff_field(message: types.Message, state: FSMContext, string_sorter: IStringSorterRepository):
    user_input = message.text.strip()
    if not user_input: return
    all_fields = list(STAFF_FIELD_MAP.keys())
    try:
        sorted_fields = await string_sorter.sort_by_similarity(user_input, all_fields)
        suggestions = sorted_fields[:3]
    except Exception:
        suggestions = [f for f in all_fields if user_input.lower() in f.lower()]

    if not suggestions:
        return await message.reply("Поле не найдено. Попробуйте ввести название заново или нажмите '✅ Сохранить обращение', чтобы завершить.")

    field_options = {STAFF_FIELD_MAP[name]: name for name in suggestions}
    await state.update_data(field_options=field_options)
    await state.set_state(StaffApplicationStates.selecting_field_other)
    await message.reply("Выберите поле из списка:", reply_markup=get_staff_field_suggestions_keyboard(field_options))

@router.callback_query(StaffFieldSelectCallback.filter(), StaffApplicationStates.selecting_field_other)
async def select_staff_field(query: types.CallbackQuery, callback_data: StaffFieldSelectCallback, state: FSMContext):
    field_key = callback_data.field_key
    field_name = STAFF_FIELD_DISPLAY.get(field_key, field_key)
    await state.update_data(editing_field_key=field_key, editing_field_name=field_name)
    await state.set_state(StaffApplicationStates.entering_value_other)
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.reply(f"✏️ Введите новое значение для *{field_name}*: ", parse_mode="Markdown")

@router.message(StaffApplicationStates.entering_value_other)
async def enter_staff_value(message: types.Message, state: FSMContext):
    new_value = message.text.strip()
    if not new_value: return await message.reply("Значение не может быть пустым.")

    data = await state.get_data()
    app_data = data.get("staff_app_data", {})
    field_key = data.get("editing_field_key")
    if field_key: app_data[field_key] = new_value
    await state.update_data(staff_app_data=app_data)
    
    await state.set_state(StaffApplicationStates.editing_other)
    text = "📄 *Обновлённые данные:*\n\n"
    for k, v in STAFF_FIELD_MAP.items():
        text += f"{k}: {app_data.get(v, '-')}\n"
    await message.answer(text + "\nВыберите действие:", parse_mode="Markdown", reply_markup=get_staff_edit_menu_keyboard())

@router.message(F.text == "✅ Сохранить обращение", StaffApplicationStates.editing_other)
async def save_without_pd(
    message: types.Message,
    state: FSMContext,
    staff_app_service: IStaffApplicationService,
    log_chat: str
):
    await _process_finalization(
        message=message,
        state=state,
        staff_app_service=staff_app_service,
        log_chat=log_chat,
        pd_agreement=False,
        pd_file_id="-"
    )

@router.message(F.text == "✅ Сохранить и перейти к ПДн", StaffApplicationStates.editing_other)
async def go_to_pd(message: types.Message, state: FSMContext):
    await state.set_state(StaffApplicationStates.pd_upload)
    await message.reply("📤 Загрузите файл с согласием на обработку ПДн или откажитесь:", reply_markup=get_pd_upload_keyboard())

@router.callback_query(StaffPdCallback.filter(), StaffApplicationStates.pd_upload)
async def choose_pd(query: types.CallbackQuery, callback_data: StaffPdCallback, state: FSMContext):
    await query.message.edit_reply_markup(reply_markup=None)
    if callback_data.action == "skip":
        await state.set_state(StaffApplicationStates.editing_other)
        await query.message.answer(
            "⏪ Вы отказались от загрузки ПДн. Вы можете отредактировать данные или сохранить обращение без согласия.",
            reply_markup=get_staff_edit_menu_keyboard()
        )
        return
    await state.set_state(StaffApplicationStates.waiting_pd_file)
    await query.message.reply("📤 Отправьте документ/фото согласия ПДн (PDF или изображение):")

@router.message(StaffApplicationStates.waiting_pd_file, F.document | F.photo)
async def receive_pd_file(
    message: types.Message,
    state: FSMContext,
    staff_app_service: IStaffApplicationService,
    log_chat: str
):
    file = message.document or message.photo[-1]
    await state.update_data(pd_agreement=True, pd_file_id=file.file_id)

    await _process_finalization(
        message=message,
        state=state,
        staff_app_service=staff_app_service,
        log_chat=log_chat,
        pd_agreement=True,
        pd_file_id=file.file_id
    )

@router.message(StaffApplicationStates.waiting_pd_file)
async def wrong_pd_type(message: types.Message):
    await message.reply("⚠️ Отправьте файл или изображение.")

async def _process_finalization(
    message: types.Message,
    state: FSMContext,
    staff_app_service: IStaffApplicationService,
    log_chat: str,
    pd_agreement: bool,
    pd_file_id: str
):
    data = await state.get_data()
    app_data = data.get("staff_app_data", {})

    logger.debug(f"Finalizing staff app for user {message.from_user.id}, data: {app_data}")
    
    try:
        staff_id = str(message.from_user.id)
        app = await staff_app_service.create_staff_application(staff_id, app_data, pd_file_id, pd_agreement)
        
        log_msg = (
            f"📩 Новое обращение от сотрудника {message.from_user.username or message.from_user.id}\n"
            f"ФИО: {app.surname} {app.name} {app.patronymic or 'Не указано'}\n"
            f"Регион: {app.region} | Город: {app.city}\n"
            f"Домашний адрес: {app.home_address or 'Не указан'}\n"
            f"Дата рождения: {app.birth_date.strftime('%d.%m.%Y')}\n"
            f"Телефон: {app.phone_number} | Email: {app.email}\n"
            f"Текст обращения:\n{app.application_text}\n"
            f"Дата из документа: {app.obtained_data_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Согласие на ПДн: {'+' if pd_agreement else '-'}\n"
            f"ID обращения: {app.id}"
        )
        
        await message.bot.send_message(chat_id=log_chat, text=log_msg)
        await message.answer("✅ Обращение успешно зарегистрировано.", reply_markup=get_menu_keyboard())
    except Exception as e:
        logger.error(f"Error saving staff application: {e}")
        await message.answer("❌ Ошибка сохранения. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()