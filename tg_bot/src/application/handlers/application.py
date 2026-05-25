import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from src.application.states import ApplicationStates
from src.application.callbacks import SendApplicationCallback, AppViewCallback
from src.application.keyboards.menu_keyboard import get_menu_keyboard
from src.application.keyboards.application_keyboard import get_application_main_keyboard, get_applications_list_keyboard
from src.services.interfaces import IApplicationService

router = Router(name=__name__)
logger = logging.getLogger(__name__)

@router.message(F.text == "Отправить обращение")
async def open_app_menu(message: types.Message):
    await message.answer(
        "Выберите способ отправки обращения:",
        reply_markup=get_application_main_keyboard()
    )

@router.callback_query(SendApplicationCallback.filter())
async def process_app_menu_callback(query: types.CallbackQuery, callback_data: SendApplicationCallback, state: FSMContext):
    await query.message.edit_text("Выбрано действие: " + callback_data.action)
    if callback_data.action == "photo":
        await query.message.answer("🚧 Функционал сканирования фото находится в разработке.")
        return
    await query.message.answer("Укажите ФИО отправителя.\nЕсли хотите отправить от своего имени, отправьте `-` или `нет`.")
    await state.set_state(ApplicationStates.sender_fio)

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
        
        # Логирование
        log_msg = f"""
📩 Новое обращение от пользователя {'@' + message.from_user.username if message.from_user.username else 'ID:' + str(message.from_user.id)}
Отправитель: {app.sender_fio or 'Используется ФИО из профиля'}
Депутат: {app.deputy_fio}
Текст:
{app.application_text}
Дата: {app.created_at.strftime('%d.%m.%Y %H:%M')}
ID обращения: {app.id}
"""
        await message.bot.send_message(chat_id=log_chat, text=log_msg)
        
        await message.answer("✅ Ваше обращение успешно зарегистрировано и отправлено.", reply_markup=get_menu_keyboard(has_applications=True))
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        await message.answer("Произошла ошибка при сохранении обращения. Попробуйте позже.")

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
