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

    def generate_response(self, base_prompt: str, prompt: str, review) -> str:
        review_text = review.text
        name = review.userName
        good = review.good
        pros = review.pros
        cons = review.cons
        valuation = review.productValuation

        result_text = f"""
                    'Обязательная часть ответа: {base_prompt if base_prompt != '' else 'Длина ответа должна быть не более 10 предложений'}'
                    ---
                    Инструкции по ответу: {prompt}
                    ---
                    Текст отзыва: {review_text}
                    ---
                    """

        if name:
            name_field = f"\nИспользуй имя клиента в отзыве: {name}\n---\n"
            result_text += name_field
        if good:
            good_field = (f"\nВот название товара, на который был сделан отзыв: {good}. "
                          f"Название товара не используй в ответе. Эта информация лишь для большего контекста.\n---\n")
            result_text += good_field
        if pros:
            pros_field = f"\nДостоинства необходимо подчеркнуть. Вот достоинства товара, которые отметил покупатель, делая свой отзыв: {pros}\n---\n"
            result_text += pros_field
        if cons:
            cons_field = f"\nНедостатки необходимо сгладить. Вот недостатки товара, которые отметил покупатель, делая свой отзыв: {cons}\n---\n"
            result_text += cons_field
        valuation_field = f"\nВот оценка товара, которую поставил покупатель: {valuation}\n---\n"
        result_text += valuation_field

        messages = [
            {
                "role": "system",
                "content": "Ты опытный специалист службы поддержки. Сгенерируй ответ на отзыв клиента на товар."
            },
            {
                "role": "user",
                "content": result_text
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