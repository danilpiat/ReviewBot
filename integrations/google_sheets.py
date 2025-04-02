import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheetsConfigManager:
    def __init__(self, sheet_id: str, creds_path: str):
        self._connect(creds_path)
        self.sheet = self.client.open_by_key(sheet_id)

    def _connect(self, creds_path):
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            self.client = gspread.authorize(creds)
        except Exception as e:
            raise ConnectionError(f"Google Sheets connection failed: {str(e)}")

    def get_active_config(self) -> dict:
        """Получает актуальные настройки из таблицы"""
        config_sheet = self.sheet.worksheet('Config')
        return {
            'ai_enabled': config_sheet.acell('B1').value == 'TRUE',
            'prompt_template': config_sheet.acell('B2').value,
            'rating_threshold': float(config_sheet.acell('B3').value)
        }