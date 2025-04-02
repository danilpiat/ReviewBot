import requests
from typing import List


class WBIntegration:
    def __init__(self, api_key: str):
        self.base_url = "https://suppliers-api.wildberries.ru"
        self.headers = {'Authorization': api_key}

    def get_new_reviews(self, rating_threshold: float) -> List[dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/reviews",
                headers=self.headers,
                params={'isAnswered': False, 'rating': rating_threshold}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"WB API error: {str(e)}")

    def post_response(self, review_id: str, response_text: str) -> bool:
        ...
