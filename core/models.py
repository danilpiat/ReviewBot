from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

@dataclass
class WbProductDetails:
    brandName: str
    nmId: int
    productName: str
    size: str
    supplierArticle: str
    imtId: Optional[int] = None  # Пример дополнительного поля
    supplierName: Optional[str] = None

    def __init__(self, **kwargs):
        self.brandName = kwargs.get('brandName', '')
        self.nmId = kwargs.get('nmId', 0)
        self.productName = kwargs.get('productName', '')
        self.size = kwargs.get('size', '')
        self.supplierArticle = kwargs.get('supplierArticle', '')

        # Дополнительные поля, которые могут быть в API
        self.imtId = kwargs.get('imtId')
        self.supplierName = kwargs.get('supplierName')


@dataclass
class WbReview:
    """Модель отзыва с основными полями и сохранением полного ответа API"""
    # Явно определенные важные поля
    id: str
    text: str
    productValuation: int
    createdDate: datetime
    productDetails: WbProductDetails
    userName: str
    bables: List[str]

    # Свойство для доступа ко всем исходным данным
    _raw_data: Dict[str, Any]  # Сделано приватным с публичным доступом через property

    def __init__(self, **kwargs):
        # Основные необходимые поля
        self.marketplace = "Wildberries"
        self.id = kwargs['id']
        self.text = kwargs.get('text', '')
        self.productValuation = kwargs['productValuation']
        self.createdDate = datetime.fromisoformat(kwargs['createdDate'].replace('Z', ''))
        self.userName = kwargs.get('userName', 'Аноним')
        self.bables = kwargs.get('bables', [])

        # Обработка вложенной структуры
        self.productDetails = WbProductDetails(**kwargs['productDetails'])

        # Сохранение всех исходных данных
        self._raw_data = kwargs

        self.good = self.productDetails.productName
        self.pros = kwargs.get('pros', '')
        self.cons = kwargs.get('cons', '')

    @property
    def metadata(self) -> Dict[str, Any]:
        """Доступ ко всем данным отзыва"""
        return self._raw_data

    @property
    def original_response(self) -> Dict[str, Any]:
        """Полный оригинальный ответ API"""
        return self._raw_data


class ResponseStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class Response:
    """Модель сгенерированного ответа"""
    id: str
    review_id: str
    response_text: str
    generated_at: datetime = datetime.now()
    sent_at: Optional[datetime] = None
    status: ResponseStatus = ResponseStatus.PENDING
    attempts: int = 0
    error_log: Optional[str] = None

    def mark_as_sent(self):
        self.status = ResponseStatus.SENT
        self.sent_at = datetime.now()

    def mark_as_failed(self, error: str):
        self.status = ResponseStatus.FAILED
        self.error_log = error
        self.attempts += 1

@dataclass
class ConfigSettings:
    """Модель настроек из Google Sheets"""
    ai_enabled: bool
    prompt_template: str
    rating_threshold: float
    response_language: str = "ru"
    max_response_length: int = 500
    last_updated: datetime = datetime.now()

    def validate(self):
        if self.rating_threshold < 0 or self.rating_threshold > 5:
            raise ValueError("Invalid rating threshold")
        if not self.prompt_template:
            raise ValueError("Prompt template cannot be empty")

@dataclass
class APIConfig:
    """Конфигурация API-ключей"""
    deepseek_api_key: str
    wildberries_api_key: str
    google_sheets_creds: dict  # JSON credentials для Google Sheets

class ValidationError(Exception):
    """Кастомное исключение для ошибок валидации"""
    def __init__(self, message: str, field: str):
        super().__init__(message)
        self.field = field
        self.message = message

    def __str__(self):
        return f"Validation error in {self.field}: {self.message}"