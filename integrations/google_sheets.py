import backoff
import gspread


class GoogleSheetsConfigManager:
    def __init__(self, sheet_id: str, creds_path: str):
        self._connect(creds_path)
        self.sheet = self.client.open_by_key(sheet_id)

    def _connect(self, creds_path):
        try:
            self.client = gspread.service_account(filename=creds_path)
        except Exception as e:
            raise ConnectionError(f"Google Sheets connection failed: {str(e)}")

    @backoff.on_exception(backoff.expo, gspread.exceptions.APIError, max_tries=3, max_time=30)
    def get_active_config(self) -> dict:
        """Получает актуальные настройки из таблицы"""
        config_sheet = self.sheet.worksheet('Настройки')
        return {
            'marketplace': config_sheet.acell('B2').value,
            'api_key': config_sheet.acell('C2').value,
            'ai_enabled': config_sheet.acell('D2').value == 'TRUE',
            'prompt_template': config_sheet.acell('E2').value,
            'rating_threshold': float(config_sheet.acell('F2').value)
        }