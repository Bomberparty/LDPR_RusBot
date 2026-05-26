from aiogram.filters.callback_data import CallbackData


class RegionCallback(CallbackData, prefix="reg"):
    region: str


class RetryRegionCallback(CallbackData, prefix="retry_reg"):
    ...


class AppViewCallback(CallbackData, prefix="app_view"):
    page: int


class FieldSelectCallback(CallbackData, prefix="field_sel"):
    field_key: str  # sender_fio, application_text, deputy_fio