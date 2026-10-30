"""
Сервис для работы с LLM моделями
"""
from typing import Optional
from config import (
    YANDEX_FOLDER_ID, YANDEX_AUTH_TOKEN, QWEN_API_KEY, GEMINI_API_KEY,
    DEFAULT_LLM_MODEL
)
from utils.logger import logger

class LLMService:
    """Сервис для работы с различными LLM моделями"""
    
    def __init__(self, model: str = None):
        self.model = model or DEFAULT_LLM_MODEL
        self._validate_config()
    
    def _validate_config(self):
        """Проверка конфигурации для выбранной модели"""
        if self.model == 'yandex' and (not YANDEX_FOLDER_ID or not YANDEX_AUTH_TOKEN):
            logger.warning("Yandex GPT: не указаны FOLDER_ID или AUTH_TOKEN")
        elif self.model == 'qwen' and not QWEN_API_KEY:
            logger.warning("Qwen: не указан API_KEY")
        elif self.model == 'gemini' and not GEMINI_API_KEY:
            logger.warning("Gemini: не указан API_KEY")
    
    def generate_response(self, prompt: str) -> str:
        """Генерация ответа на основе промпта"""
        try:
            if self.model == 'yandex':
                return self._generate_yandex(prompt)
            elif self.model == 'qwen':
                return self._generate_qwen(prompt)
            elif self.model == 'gemini':
                return self._generate_gemini(prompt)
            else:
                logger.error(f"Неизвестная модель: {self.model}")
                return "Извините, произошла ошибка при генерации ответа."
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}", exc_info=True)
            return "Извините, произошла ошибка при генерации ответа. Попробуйте позже."
    
    def _generate_yandex(self, prompt: str) -> str:
        """Генерация через Yandex GPT"""
        try:
            from yandex_cloud_ml_sdk import YCloudML
            
            sdk = YCloudML(
                folder_id=YANDEX_FOLDER_ID,
                auth=YANDEX_AUTH_TOKEN,
            )
            model = sdk.models.completions("yandexgpt-lite")
            model = model.configure(temperature=0.2)
            result = model.run(prompt)
            answer = result.alternatives[0].text
            answer = answer.replace("*", "")
            return answer
        except Exception as e:
            logger.error(f"Ошибка Yandex GPT: {e}")
            raise
    
    def _generate_qwen(self, prompt: str) -> str:
        """Генерация через Qwen"""
        try:
            from qwen_api.client import Qwen
            from qwen_api.core.types.chat import ChatMessage
            
            client = Qwen(api_key=QWEN_API_KEY, cookie="")
            messages = [
                ChatMessage(
                    role="user",
                    content=prompt,
                    web_search=True,
                    thinking=False,
                )
            ]
            response = client.chat.create(
                messages=messages,
                model="qwen-max-latest",
            )
            return str(response)
        except Exception as e:
            logger.error(f"Ошибка Qwen: {e}")
            raise
    
    def _generate_gemini(self, prompt: str) -> str:
        """Генерация через Gemini"""
        try:
            from google import genai
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Ошибка Gemini: {e}")
            raise
