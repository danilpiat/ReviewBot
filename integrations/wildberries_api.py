import time

import requests
from typing import List, Optional

FEEDBACKS_URL = "/api/v1/feedbacks"
ANSWER_TO_FEEDBACK_URL = "/api/v1/feedbacks/answer"

class WBIntegration:
    def __init__(self, api_key: str):
        self.base_url = "https://feedbacks-api.wildberries.ru"
        self.headers = {'Authorization': api_key}
        self.state = ["wbRu"] #только прошедшие проверку WB отзывы (прошли модерацию от Wb)
        self.last_request_time: Optional[float] = None

    def get_new_reviews(self, rating_threshold: int) -> List[dict]:
        try:
            response = requests.get(
                self.base_url+FEEDBACKS_URL,
                headers=self.headers,
                params={'isAnswered': True, 'take': 5000, 'skip': 0} #TODO сменить на False
            )
            response.raise_for_status()
            return self._filter_by_state_and_threshold(response.json(), rating_threshold)
        except Exception as e:
            raise ConnectionError(f"WB API error: {str(e)}")

    def _filter_by_state(self, review):
        return True if review['state'] in self.state else False

    def _filter_by_state_and_threshold(self, data, rating_threshold: int) -> List[dict]:
        new_reviews = []
        reviews = data['data']['feedbacks']
        for review in reviews:
            if self._filter_by_state(review) and review['productValuation'] > rating_threshold:
                new_reviews.append(review)
        return new_reviews

    def post_response(self, review_id: str, response_text: str) -> bool:
        """
        Отправляет ответ на отзыв через Wildberries API
        Возвращает True при успешной отправке, False при ошибке
        """
        try:
            self._rate_limit()

            payload = {
                "id": review_id,
                "text": response_text[:5000]  # Обрезаем текст до 5000 символов
            }

            response = requests.post(
                url=self.base_url+ANSWER_TO_FEEDBACK_URL,
                headers=self.headers,
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            return True

        except Exception as e:
            raise e
        finally:
            self.last_request_time = time.time()

    def _rate_limit(self):
        """Контроль ограничения скорости запросов"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < 1.0:
                sleep_time = 1.0 - elapsed
                time.sleep(sleep_time)
