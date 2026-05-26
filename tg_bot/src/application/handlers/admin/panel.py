import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from src.application.states import AdminStates
from src.application.callbacks import AdminPanelCallback
from src.application.keyboards.admin_panel_keyboard import get_admin_panel_keyboard
from src.services.interfaces import IUserService
from src.domain.exceptions import UserNotFoundError
from src.domain.entities.user import Role

router = Router(name=__name__)
logger = logging.getLogger(__name__)

@router.message(F.text == "Админ-панель")
async def open_admin_panel(message: types.Message, state: FSMContext):
    await state.set_state(AdminStates.menu)
    await message.answer("🛡️ <b>Админ-панель</b>\nВыберите действие:", parse_mode="HTML", reply_markup=get_admin_panel_keyboard())

@router.callback_query(AdminPanelCallback.filter(), AdminStates.menu)
async def handle_admin_action(query: types.CallbackQuery, callback_data: AdminPanelCallback, state: FSMContext):
    if callback_data.action == "promote_staff":
        await query.message.answer("Введите ID пользователя (только цифры), которого нужно повысить до Сотрудника:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(AdminStates.promote_to_staff)
    await query.answer()

@router.message(AdminStates.promote_to_staff)
async def process_promote_to_staff(message: types.Message, state: FSMContext, user_service: IUserService):
    try:
        target_user_id = int(message.text.strip())
    except ValueError:
        return await message.reply("❌ ID должен состоять только из цифр. Попробуйте ещё раз или вернитесь в меню.")

    try:
        await user_service.update_user_role(target_user_id, Role.STAFF)
        await message.reply(f"✅ Пользователь с ID `{target_user_id}` успешно повышен до Сотрудника.", parse_mode="HTML")
    except UserNotFoundError:
        await message.reply("❌ Пользователь с таким ID не найден в системе.")
    except Exception as e:
        logger.error(f"Failed to update role for user {target_user_id}: {e}")
        await message.reply("❌ Произошла ошибка при изменении роли. Попробуйте позже.")

    # Возвращаемся в меню админа
    await state.set_state(AdminStates.menu)
    await message.answer("Выберите действие:", reply_markup=get_admin_panel_keyboard())