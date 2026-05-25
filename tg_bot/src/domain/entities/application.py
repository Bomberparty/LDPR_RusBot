from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Application:
    id: int
    user_id: int
    sender_fio: str | None
    deputy_fio: str
    application_text: str
    created_at: datetime = field(default_factory=datetime.now)
