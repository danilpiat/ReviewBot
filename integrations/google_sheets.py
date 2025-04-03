from typing import Dict, List, Any
from utils.logger import AppLogger

import backoff
import gspread


class GoogleSheetsConfigManager:
    def __init__(self, sheet_id: str, creds_path: str, logger: AppLogger) -> None:
        self._connect(creds_path)
        self.sheet = self.client.open_by_key(sheet_id)
        self._header_mapping: Dict[str, str] = None
        self.logger = logger

    def _connect(self, creds_path):
        try:
            self.client = gspread.service_account(filename=creds_path)
        except Exception as e:
            raise ConnectionError(f"Google Sheets connection failed: {str(e)}")

    @backoff.on_exception(backoff.expo, gspread.exceptions.APIError, max_tries=3, max_time=30)
    def _load_config_sheet(self) -> List[Dict[str, Any]]:
        """Загружает и парсит данные из основного листа конфигурации"""
        worksheet = self.sheet.worksheet('Настройки')
        raw_data = worksheet.get_all_values()

        if len(raw_data) < 2:
            raise ValueError("Таблица на листе 'Настройки' должна содержать хотя бы 2 строки.")

        headers = [cell.strip() for cell in raw_data[0]]
        self._header_mapping = {header: idx for idx, header in enumerate(headers)}

        return [
            {header: row[idx] for header, idx in self._header_mapping.items()}
            for row in raw_data[1:]
        ]

    def _parse_base_config(self, config_data: List[Dict]) -> List[Dict]:
        """Парсит базовую конфигурацию из первой строки данных"""
        if not config_data:
            raise ValueError("No configuration data found")

        configs = []
        required_fields = {'Маркетплейс', 'API ключ', 'Активировать ИИ', 'Отвечаем на отзывы с оценкой более', 'Ключ ИИ'}
        marketplaces = []
        for idx, row in enumerate(config_data, start=2):  # Строки нумеруются с 2 (заголовок в 1 строке)
                missing_fields = required_fields - row.keys()
                if missing_fields:
                    raise ValueError(f"Missing required fields in row {idx}: {', '.join(missing_fields)}")

                # Основные параметры
                config = {
                    'marketplace': row['Маркетплейс'].strip(),
                    'api_key': row['API ключ'].strip(),
                    'ai_key': row['Ключ ИИ'].strip(),
                    'rating_threshold': float(row.get('Отвечаем на отзывы с оценкой более', 3)),
                    'ai_enabled': row.get('Активировать ИИ', '').upper() == 'TRUE',
                    'prompt_template': row.get('Вариант промпта', '').strip(),
                }

                # # Дополнительные параметры
                # optional_fields = {
                #     'Дополнительные настройки': 'additional_settings',
                #     'Лимит ответов': 'response_limit'
                # }
                #
                # for sheet_field, config_field in optional_fields.items():
                #     if sheet_field in row:
                #         config[config_field] = row[sheet_field].strip()
                if config['marketplace'] not in marketplaces:
                    configs.append(config)
                    marketplaces.append(config['marketplace'])
                else:
                    self.logger.logger.warning(f"Маркетплейс {config['marketplace']} уже есть в config. Возможно в таблице дубликат.")

        if not configs:
            raise ValueError("No valid configurations found in the sheet")

        return configs

    @backoff.on_exception(backoff.expo, gspread.exceptions.APIError, max_tries=3, max_time=30)
    def _load_prompt_options(self) -> Dict[str, str]:
        """Загружает варианты промптов из связанного листа"""
        try:
            prompt_ws = self.sheet.worksheet('Промпт ответов на отзывы')
            prompt_data = prompt_ws.get_all_values()

            if len(prompt_data) < 2:
                return {}

            options_header = [cell.strip() for cell in prompt_data[0]]
            options_values = prompt_data[1]

            return {
                header: value
                for header, value in zip(options_header, options_values)
                if header and value
            }
        except gspread.WorksheetNotFound:
            return {}

    @backoff.on_exception(backoff.expo, gspread.exceptions.APIError, max_tries=3, max_time=30)
    def get_active_config(self) -> dict:
        """Получает конфигурацию из Google Sheets в виде словаря"""
        config_data = self._load_config_sheet()
        config = self._parse_base_config(config_data)

        if 'Вариант промпта' in self._header_mapping:
            prompt_options = self._load_prompt_options()
            if 'Обязательная часть' not in prompt_options:
                raise Exception("В листе 'Промпт ответов на отзывы' должен быть промпт в столбце 'Обязательная часть'")
            for row in config:
                row['prompt_options'] = prompt_options

        return config