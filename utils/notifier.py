import requests


class NotificationManager:
    def __init__(self, bot_token: str, chat_id: str = "5125197365"):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_alert(self, message: str, level: str = "INFO"):
        """Отправляет уведомление в Telegram чат"""
        try:
            formatted_message = f"*{level}*\n{message}"

            payload = {
                "chat_id": self.chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }

            response = requests.post(
                self.telegram_api_url,
                json=payload,
                timeout=20
            )
            response.raise_for_status()

        except Exception as e:
            print(f"Failed to send Telegram notification: {str(e)}")