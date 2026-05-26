from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Application:
    id: int
    user_id: int
    application_text: str
    created_at: datetime = field(default_factory=datetime.now)