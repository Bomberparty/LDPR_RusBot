from dataclasses import dataclass, field
from datetime import datetime, date

@dataclass
class StaffApplication:
    id: str
    staff_id: str
    surname: str
    name: str
    patronymic: str | None
    region: str
    city: str
    home_address: str | None
    birth_date: date
    phone_number: str
    email: str
    source: str
    obtained_data_at: datetime
    application_text: str
    personal_data_agreement: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now())
    application_file_id: str = "-"
    personal_data_file_id: str = "-"