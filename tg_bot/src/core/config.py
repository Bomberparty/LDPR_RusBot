import json
import os

from dotenv import load_dotenv

load_dotenv()
TG_API_TOKEN = os.getenv("TG_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROXY_URL_FOR_SDK = os.getenv("PROXY_URL_FOR_SDK")
proxy = os.getenv("PROXY", None)

log_chat = os.getenv("LOG_CHAT")
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", None)
log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
admin_ids = json.loads(os.getenv("ADMIN_IDS", '[]'))