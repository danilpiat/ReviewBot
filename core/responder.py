from typing import Optional
from integrations.deepseek_api import AIResponseGenerator
from core.models import Review


class ReviewResponder:
    def __init__(self, ai_client: AIResponseGenerator, logger: AppLogger):
        self.ai_client = ai_client
        self.logger = logger

    def process_review(self, review: Review, prompt: str) -> Optional[str]:
        try:
            self.logger.info("Processing review", {"review_id": review.id})

            if not self._validate_review(review):
                return None

            response = self.ai_client.generate_response(prompt, review.text)
            self._post_process(response)

            return response
        except Exception as e:
            self.logger.error("Review processing failed", {
                "error": str(e),
                "review_id": review.id
            })
            return None

    def _validate_review(self, review: Review) -> bool:
        # Дополнительные проверки
        return True

    def _post_process(self, response: str):
        # Пост-обработка ответа
        pass