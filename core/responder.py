import traceback
from typing import Optional
from integrations.deepseek_api import AIResponseGenerator
from core.models import WbReview
from utils import AppLogger


class ReviewResponder:
    def __init__(self, ai_client: AIResponseGenerator, logger: AppLogger):
        self.ai_client = ai_client
        self.logger = logger.logger

    def process_review(self, review: Optional[WbReview], base_prompt: str, prompt: str) -> Optional[str]:
        try:
            self.logger.info(f"[{review.marketplace}] Обрабатываю отзыв с id {review.id}")

            # if not self._validate_review(review):
            #     self.logger.info(f"[{review.marketplace}] [{review.id}] Текст отзыва пустой.")
            #     return None

            response = self.ai_client.generate_response(base_prompt, prompt, review)
            self.logger.info(f"[{review.marketplace}] [{review.id}] Ответ ИИ: '''{response}''' ")
            if self._post_process(response):
                return response
            else:
                self.logger.error(f"[{review.marketplace}] [{review.id}] Текст ответа от ИИ не прошел пост-валидацию.")
        except Exception as e:
            self.logger.error(f"[{review.marketplace}] [{review.id}] Review processing failed. " + traceback.format_exc())
            return None

    def _validate_review(self, review: WbReview) -> bool:
        # Дополнительные проверки
        if not review.text.strip():
            return False
        return True

    def _post_process(self, response: str):
        words = response.split()
        if len(words) <= 4 or not isinstance(response, str) or not response.strip() or len(response) >= 5000:
            return False
        return True