import os
from datetime import datetime
from http.cookies import SimpleCookie

from curl_cffi import requests
import json
import time
from typing import List, Dict, Optional
import backoff
from curl_cffi.requests.exceptions import RequestException


class OzonIntegration:
    def __init__(self, cookies_path: str, company_id: str):
        self.base_url = "https://seller.ozon.ru"
        self.company_id = company_id
        self.cookies_path = cookies_path
        self.all_companies_cookies = self._load_all_cookies()
        self.cookies = self._get_company_cookies()
        self.headers = self._prepare_headers()
        self.last_request_time: Optional[float] = None
        self.rate_limit_delay = 2  # Более консервативный интервал для Ozon

    def _load_all_cookies(self) -> dict:
        """Загружает все cookies для всех компаний из файла"""
        if not os.path.exists(self.cookies_path):
            raise FileNotFoundError(f"Cookies file not found: {self.cookies_path}")

        try:
            with open(self.cookies_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in cookies file")
        except Exception as e:
            raise RuntimeError(f"Error loading cookies: {str(e)}")

    def _get_company_cookies(self) -> dict:
        """Получает cookies для текущей компании"""
        cookies = self.all_companies_cookies.get(self.company_id)
        if not cookies:
            raise ValueError(f"No cookies found for company ID: {self.company_id}")
        return cookies

    def _prepare_headers(self) -> dict:
        """Формирует заголовки с динамическими cookies"""
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru",
            "content-type": "application/json",
            "cookie": "; ".join([f"{k}={v}" for k, v in self.cookies.items()]),
            "origin": "https://seller.ozon.ru",
            "priority": "u=1, i",
            "referer": "https://seller.ozon.ru/app/reviews",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "YaBrowser";v="25.2", "Yowser";v="2.5"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 YaBrowser/25.2.0.0 Safari/537.36",
            "x-o3-app-name": "seller-ui",
            "x-o3-company-id": f"{self.company_id}",
            "x-o3-language": "ru",
            "x-o3-page-type": "review"
        }

    def iso_to_microtimestamp(self, iso_str: str) -> int:
        """Конвертирует ISO строку в микросекундный timestamp"""
        dt = datetime.fromisoformat(iso_str.replace('Z', ''))
        return int(dt.timestamp() * 1_000_000)

    def get_new_reviews(self, rating_threshold: int) -> List[dict]:
        """Получает все непросмотренные отзывы с пагинацией"""
        all_reviews = []
        last_timestamp = None
        last_uuid = None

        # while True:
        chunk, last_timestamp, last_uuid = self._get_reviews_chunk(
            rating_threshold,
            last_timestamp,
            last_uuid
        )
            # if not chunk:
            #     break

        all_reviews.extend(chunk)

        return all_reviews

    @backoff.on_exception(backoff.expo,
                          (RequestException, ConnectionError),
                          max_tries=3,
                          max_time=30)
    def _get_reviews_chunk(self, rating_threshold: int,
                           last_timestamp: Optional[str],
                           last_uuid: Optional[str]) -> (List[dict], str, str):
        """Получает одну страницу отзывов"""
        self._rate_limit()

        payload = {
            "with_counters": False,
            "sort": {
                "sort_by": "PUBLISHED_AT",
                "sort_direction": "DESC"
            },
            "company_type": "seller",
            "filter": {
                "rating": [i for i in range(int(rating_threshold), 5 + 1)],
                "interaction_status": ["NOT_VIEWED"]
            },
            "company_id": self.company_id,
            "pagination_last_timestamp": last_timestamp,
            "pagination_last_uuid": last_uuid
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v3/review/list",
                headers=self.headers,
                json=payload,
                impersonate="chrome120",
                timeout=15
            )
            response.raise_for_status()

            if 'set-cookie' in response.headers:
                new_cookies = self._parse_cookies(response.headers['set-cookie'])
                self._update_cookies(new_cookies)

            data = response.json()
            l_timestamp = data['pagination_last_timestamp']
            l_uuid = data['pagination_last_uuid']
            return [r for r in data.get("result", []) if r.get("rating") >= rating_threshold], l_timestamp, l_uuid

        except Exception as e:
            raise ConnectionError(f"Ozon API error: {str(e)}")

    def _parse_cookies(self, cookie_header: str) -> dict:
        """Парсит cookies из заголовка Set-Cookie"""
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        return {k: v.value for k, v in cookie.items()}

    def _update_cookies(self, new_cookies: dict):
        """Обновляет cookies в памяти и сохраняет в файл"""
        # Обновляем cookies для текущей компании
        self.cookies.update(new_cookies)
        self.all_companies_cookies[self.company_id] = self.cookies

        # Сохраняем все компании обратно в файл
        try:
            with open(self.cookies_path, 'w') as f:
                json.dump(self.all_companies_cookies, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save cookies: {str(e)}")

        # Обновляем заголовки
        self.headers['cookie'] = "; ".join(
            [f"{k}={v}" for k, v in self.cookies.items()]
        )

    backoff.on_exception(backoff.expo,
                         (RequestException, ConnectionError),
                         max_tries=3,
                         max_time=30)
    def post_response(self, review_uuid: str, response_text: str) -> bool:
        """Отправляет ответ на отзыв в Ozon"""
        self._rate_limit()

        payload = {
            "text": response_text[:2000],  # Ozon допускает до 2000 символов
            "review_uuid": review_uuid,
            "company_type": "seller",
            "company_id": self.company_id
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/review/comment/create",
                headers=self.headers,
                json=payload,
                impersonate="chrome120",
                timeout=15
            )

            if response.status_code == 200:
                return True
            return False

        except Exception as e:
            raise ConnectionError(f"Ozon post response failed: {str(e)}")

    def _rate_limit(self):
        """Контроль ограничений API Ozon"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()