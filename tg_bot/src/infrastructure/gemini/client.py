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
        
        self._regular_prompt = (
            "Extract the application text from the provided document image as a strict JSON object:\n"
            "- application_text: The main text/content of the application\n"
            "Return ONLY a valid JSON object with exactly this one key. "
            "If the field is missing or unclear, set its value to null."
        )
        
        self._staff_prompt = (
            "Extract data from the provided application document image as a strict JSON object.\n"
            "Fields to extract:\n"
            "- surname: string\n- name: string\n- patronymic: string (null if missing)\n"
            "- region: string\n- city: string\n- home_address: string (null if missing)\n"
            "- birth_date: string (format DD.MM.YYYY)\n- phone_number: string\n"
            "- email: string\n- application_text: string\n"
            "- obtained_data_at: string (date/time found in the document, format DD.MM.YYYY HH:MM or null)\n"
            "Return ONLY a valid JSON object. If a field is missing or unclear, set its value to null."
        )

    async def extract_application_data(self, image_bytes: bytes) -> dict[str, str]:
        return await self._call_gemini(image_bytes, self._regular_prompt)

    async def extract_staff_application_data(self, image_bytes: bytes) -> dict:
        raw = await self._call_gemini(image_bytes, self._staff_prompt, parse_json=True)
        return raw

    async def _call_gemini(self, image_bytes: bytes, prompt: str, parse_json: bool = False) -> dict:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            raw_json = response.text.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json.split("```json")[1].split("```")[0].strip()
            elif raw_json.startswith("```"):
                raw_json = raw_json.split("```")[1].strip()
                
            data = json.loads(raw_json)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            raise ValueError("Не удалось распознать структуру ответа нейросети")
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            raise