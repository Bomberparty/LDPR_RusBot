from aiogram.filters.callback_data import CallbackData


class RegionCallback(CallbackData, prefix="reg"):
    region: str


class RetryRegionCallback(CallbackData, prefix="retry_reg"):
    ...


class AppViewCallback(CallbackData, prefix="app_view"):
    page: int


class FieldSelectCallback(CallbackData, prefix="field_sel"):
    field_key: str  # sender_fio, application_text, deputy_fio


class AdminPanelCallback(CallbackData, prefix="admin_panel"):
    action: str


class StaffScanTypeCallback(CallbackData, prefix="staff_scan"):
    action: str  # "my" | "other"


class StaffFieldSelectCallback(CallbackData, prefix="staff_field_sel"):
    field_key: str


class StaffPdCallback(CallbackData, prefix="staff_pd"):
    action: str  # "upload" | "skip"