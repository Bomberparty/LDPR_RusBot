from aiogram.fsm.state import StatesGroup, State


class RegistrationStates(StatesGroup):
    personal_data = State()
    membership = State()
    surname = State()
    name = State()
    gender = State()
    patronymic = State()
    birth_date = State()
    phone = State()
    email = State()
    region_by_text = State()
    region_by_button = State()
    city = State()
    wish_to_join = State()
    home_address = State()
    news_subscription = State()


class PostsStates(StatesGroup):
    get_message = State()
    confirm = State()


class UploadVideoStates(StatesGroup):
    location = State()
    video = State()
    uploading = State()


class ApplicationPhotoStates(StatesGroup):
    waiting_photo = State()
    editing = State()
    typing_field = State()
    selecting_field = State()
    entering_value = State()


class StaffApplicationStates(StatesGroup):
    choice_type = State()
    waiting_photo_other = State()
    editing_other = State()
    typing_field_other = State()
    selecting_field_other = State()
    entering_value_other = State()
    pd_upload = State()
    waiting_pd_file = State()
    confirm_save = State()


class AdminStates(StatesGroup):
    menu = State()
    promote_to_staff = State()