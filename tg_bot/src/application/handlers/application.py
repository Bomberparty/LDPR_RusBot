import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from src.application.states import ApplicationPhotoStates, StaffApplicationStates
from src.application.callbacks import AppViewCallback, FieldSelectCallback
from src.application.keyboards.menu_keyboard import get_menu_keyboard
from src.application.keyboards.application_keyboard import (
    get_edit_menu_keyboard,
    get_field_suggestions_keyboard,
    get_applications_list_keyboard
)
from src.services.interfaces import IApplicationService
from src.domain.interfaces import IGeminiExtractor, IStringSorterRepository, IUserRepository, IUnitOfWork
from src.domain.entities import Sources

router = Router(name=__name__)
logger = logging.getLogger(__name__)

FIELD_MAP = {
    "Текст обращения": "application_text"
}
FIELD_DISPLAY_NAMES = {v: k for k, v in FIELD_MAP.items()}


@router.message(F.text == "Сканировать обращение")
async def start_scan_application(message: types.Message, state: FSMContext, user_repository: IUserRepository, admin_ids: list[int]):
    await state.clear()
    
    is_staff = message.from_user.id in admin_ids
    if not is_staff:
        try:
            user = await user_repository.get_user(message.from_user.id, Sources.TG)
            is_staff = user.role.value in ["staff", "admin"]
        except Exception:
            is_staff = False

    if is_staff:
        await state.set_state(StaffApplicationStates.choice_type)
        return await message.answer("Выберите тип сканирования: ", reply_markup=get_menu_keyboard()) # Note: staff menu is handled in other router usually, but keeping structure
    
    await state.set_state(ApplicationPhotoStates.waiting_photo)
    await message.answer("📷 Пожалуйста, отправьте чёткое фото обращения...")


@router.message(ApplicationPhotoStates.waiting_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext, gemini_extractor: IGeminiExtractor):
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_bytes = (await message.bot.download_file(file_info.file_path)).read()

    await message.answer("🔄 Начинаю обработку фото... Это может занять несколько секунд.")
    try:
        extracted = await gemini_extractor.extract_application_data(file_bytes)
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")
        await message.answer("❌ Ошибка анализа фото нейросетью. Попробуйте отправить другое изображение.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    await state.update_data(app_photo_data=extracted)
    await state.set_state(ApplicationPhotoStates.editing)

    text = (
        f"📄 *Распознанные данные обращения:*\n\n"
        f"📝 *Текст обращения:* {extracted.get('application_text', '-')}\n\n"
        f"Выберите действие: сохраните обращение или отредактируйте текст."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_edit_menu_keyboard())


@router.message(ApplicationPhotoStates.waiting_photo)
async def wrong_photo_type(message: types.Message):
    await message.reply("⚠️ Пожалуйста, отправьте именно фотографию или изображение документа.")


@router.message(F.text == "✏️ Отредактировать", ApplicationPhotoStates.editing)
async def start_edit_field(message: types.Message, state: FSMContext):
    await state.set_state(ApplicationPhotoStates.typing_field)
    await message.reply("Начните вводить название поля для редактирования:")


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
    await query.message.reply(f"✏️ Введите новое значение для *{field_name}*: ", parse_mode="Markdown")


@router.message(ApplicationPhotoStates.entering_value)
async def enter_new_value(message: types.Message, state: FSMContext):
    new_value = message.text.strip()
    if not new_value:
        return await message.reply("Значение не может быть пустым.")

    data = await state.get_data()
    app_data = data.get("app_photo_data", {})
    field_key = data.get("editing_field_key")

    if field_key:
        app_data[field_key] = new_value
        await state.update_data(app_photo_data=app_data)

    await state.set_state(ApplicationPhotoStates.editing)

    text = (
        f"📄 *Обновлённые данные:*\n\n"
        f"📝 *Текст обращения:* {app_data.get('application_text', '-')}\n\n"
        f"Выберите действие:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_edit_menu_keyboard())


@router.message(F.text == "✅ Сохранить обращение", ApplicationPhotoStates.editing)
async def save_photo_application(
    message: types.Message, 
    state: FSMContext, 
    app_service: IApplicationService, 
    user_repository: IUserRepository, 
    log_chat: str,
    uow: IUnitOfWork
):
    data = await state.get_data()
    app_data = data.get("app_photo_data")

    if not app_data:
        return await message.reply("❌ Ошибка: данные обращения не найдены.", reply_markup=ReplyKeyboardRemove())

    try:
        async with uow.atomic():
            user = await user_repository.get_user(message.from_user.id, Sources.TG)
            app = await app_service.create_application(
                user_id=message.from_user.id,
                text=app_data.get("application_text", "-")
            )

        pd_status = "+"
        
        log_msg = (
            f"📩 Новое обращение от пользователя {f'@{message.from_user.username}' if message.from_user.username else f'ID:{message.from_user.id}'}\n"
            f"ФИО: {user.surname} {user.name} {user.patronymic or 'Не указано'}\n"
            f"Регион: {user.region} | Город: {user.city}\n"
            f"Дата рождения: {user.birth_date.strftime('%d.%m.%Y')}\n"
            f"Телефон: {user.phone_number} | Email: {user.email}\n"
            f"Текст обращения:\n{app.application_text}\n"
            f"Дата обращения: {app.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"ID обращения: {app.id}"
        )
        await message.bot.send_message(chat_id=log_chat, text=log_msg)

        await message.answer("✅ Ваше обращение успешно зарегистрировано.", reply_markup=get_menu_keyboard(has_applications=True))
    except Exception as e:
        logger.error(f"Error saving photo application: {e}")
        await message.answer("❌ Ошибка сохранения. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()


@router.message(F.text == "Мои обращения")
async def view_my_apps(message: types.Message, app_service: IApplicationService):
    apps, count = await app_service.get_user_applications(message.from_user.id, page=0)
    if not apps:
        return await message.answer("У вас пока нет обращений.")
    await message.answer(f"📂 Ваши обращения (всего: {count}):", reply_markup=get_applications_list_keyboard(apps, page=0, total_count=count))


@router.callback_query(AppViewCallback.filter())
async def paginate_apps(query: types.CallbackQuery, callback_data: AppViewCallback, app_service: IApplicationService):
    apps, count = await app_service.get_user_applications(query.from_user.id, page=callback_data.page)
    await query.message.edit_reply_markup(reply_markup=get_applications_list_keyboard(apps, callback_data.page, count))