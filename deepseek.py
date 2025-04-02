import os
import requests
from openai import OpenAI

DEEPSEEK_API_URL = "https://hubai.loe.gg/v1"
DEEPSEEK_API_KEY = "sk-Hf5sYl71ZmRT9bjwLkQViQ"

client = OpenAI(
api_key="sk-Hf5sYl71ZmRT9bjwLkQViQ",
base_url="https://hubai.loe.gg/v1"
)
def generate_review_response(prompt: str, review: str) -> str:
    """
    Генерирует ответ на отзыв о товаре с использованием DeepSeek API

    :param prompt: Инструкции по формату и стилю ответа
    :param review: Текст отзыва от пользователя
    :return: Сгенерированный ответ
    """

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
            Текст отзыва: {review}
            ---
            Сгенерируй профессиональный ответ:
            """
        }
    ]


    response = client.chat.completions.create(
        model="deepseek-chat-fast",
        messages=messages,
        temperature=0.7,
        timeout = 10

    # ,stream=True
    )

    try:
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка при генерации ответа: {str(e)}"


# Пример использования
if __name__ == "__main__":
    response_prompt = """Учти следующие требования:
    - Ответ должен быть вежливым
    - Предложи решение проблемы
    - Сохрани профессиональный тон"""

    customer_review = """
   Спасибо, всё подошло
   """

    generated_response = generate_review_response(response_prompt, customer_review)
    print("Сгенерированный ответ:")
    print(generated_response)