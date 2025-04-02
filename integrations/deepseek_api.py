import os
import requests
from openai import OpenAI


class AIResponseGenerator:
    def __init__(self, api_key: str):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://hubai.loe.gg/v1"
        )

    def generate_response(self, prompt: str, review_text: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Ты опытный специалист службы поддержки. Сгенерируй ответ на отзыв клиента."
            },
            {
                "role": "user",
                "content": f"""
                    Инструкции по ответу: {prompt}
                    ---
                    Текст отзыва: {review_text}
                    ---
                    Сгенерируй профессиональный ответ:
                    """
            }
        ]

        response = self.client.chat.completions.create(
            model="deepseek-chat-fast",
            messages=messages,
            temperature=0.7,
            timeout=10

            # ,stream=True
        )

        try:
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при генерации ответа: {str(e)}"