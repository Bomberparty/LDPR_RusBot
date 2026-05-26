import json
import logging
from google import genai
from google.genai import types
from src.domain.interfaces import IGeminiExtractor

logger = logging.getLogger(__name__)

class GeminiExtractor(IGeminiExtractor):
    def __init__(self, api_key: str, proxy_url_for_sdk: str):
        sdk_http_options = types.HttpOptions(        
            client_args={'proxy': proxy_url_for_sdk},        
            async_client_args={'proxy': proxy_url_for_sdk},        
        )
        self.client = genai.Client(        
            api_key=api_key,        
            http_options=sdk_http_options        
        )
        self.model = "gemini-2.5-flash"
        self.prompt = (
            "Extract the application text from the provided document image as a strict JSON object:\n"
            "- application_text: The main text/content of the application\n"
            "Return ONLY a valid JSON object with exactly this one key.  "
            "If the field is missing or unclear, set its value to null."
        )

    async def extract_application_data(self, image_bytes: bytes) -> dict[str, str]:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    self.prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            raw_json = response.text.strip()
            # Убираем markdown-обёртку, если нейросеть её добавила
            if raw_json.startswith("```json"):
                raw_json = raw_json.split("```json")[1].split("```")[0].strip()
            elif raw_json.startswith("```"):
                raw_json = raw_json.split("```")[1].strip()
                
            data = json.loads(raw_json)
            
            return {
                "application_text": data.get("application_text") or "-",
            }
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            raise ValueError("Не удалось распознать структуру ответа нейросети")
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            raise