import os
import requests
from openai import OpenAI


class AIResponseGenerator: #TODO сделать обработку случая, когда закончились деньги на аккаунте
    def __init__(self, api_key: str):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://hubai.loe.gg/v1"
        )

    def generate_response(self, base_prompt: str, prompt: str, review_text: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Ты опытный специалист службы поддержки. Сгенерируй ответ на отзыв клиента."
            },
            {
                "role": "user",
                "content": f"""
                    'Обязательная часть ответа: {base_prompt if base_prompt != '' else 'Длина ответа должна быть не более 10 предложений'}'
                    ---
                    Инструкции по ответу: {prompt}
                    ---
                    Текст отзыва: {review_text}
                    ---
                    Сгенерируй профессиональный ответ. Нужен только текст ответа длинной не более 5000 символов:
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
            return ''