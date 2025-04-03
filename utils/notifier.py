import telebot
import re
from typing import Optional


class NotificationManager:
    def __init__(self, bot_token: str, chat_id: str = "5125197365"):
        self.bot = telebot.TeleBot(bot_token)
        self.chat_id = chat_id
        # Регулярные выражения для валидации
        self._markdown_chars = re.compile(r"([_*\[\]()~`>#+\-=|{}.!])")
        self._entity_pattern = re.compile(r"\[(.*?)\]\((.*?)\)")

    def send_alert(self, message: str, level: str = "INFO"):
        """Безопасная отправка сообщений с автоматическим экранированием"""
        try:
            safe_message = self._sanitize_message(message)
            formatted_message = self._format_message(safe_message, level)

            self.bot.send_message(
                chat_id=self.chat_id,
                text=formatted_message,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
                disable_notification=level != "CRITICAL"
            )

        except Exception as e:
            print(f"Notification error: {str(e)} | Original message: {message[:200]}...")

    def _sanitize_message(self, text: str, max_length: int = 4000) -> str:
        """Очистка и подготовка текста для Telegram"""
        text = text.strip()[:max_length]

        text = self._markdown_chars.sub(r"\\\1", text)

        text = self._fix_links(text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _format_message(self, text: str, level: str) -> str:
        """Форматирование сообщения с учетом уровня важности"""
        level_icons = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }

        icon = level_icons.get(level, "🔔")
        header = f"{icon} *{self._sanitize_header(level)}*"

        return f"{header}\n\n{text}"

    def _sanitize_header(self, text: str) -> str:
        """Дополнительная обработка заголовка"""
        return text.upper().replace(".", "").replace("!", "")

    def _fix_links(self, text: str) -> str:
        """Валидация и исправление Markdown ссылок"""

        def _replace_link(match):
            title = self._markdown_chars.sub(r"\\\1", match.group(1))
            url = match.group(2)
            if not url.startswith(("http://", "https://")):
                return title
            return f"[{title}]({url})"

        return self._entity_pattern.sub(_replace_link, text)