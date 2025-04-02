import time
import traceback

from gspread import api_key

from core import WbReview
from integrations.google_sheets import GoogleSheetsConfigManager
from integrations.wildberries_api import WBIntegration
from integrations.deepseek_api import AIResponseGenerator
from utils import NotificationManager
from utils.logger import AppLogger
from core.responder import ReviewResponder


def main():
    # Инициализация компонентов
    logger = AppLogger("MainApp")


    while True:
        notifier = NotificationManager(
            bot_token="8036852376:AAHgYOoYzvalPzwcIf5F0TYAkM-FjGRyGMg",  # Замените на реальный токен
            chat_id="5125197365"
        )
        logger.logger.info("Начинаю проход по циклу")
        try:
            config = GoogleSheetsConfigManager("1QZw7vZIZR6caHJwGu0zwdp5K8TSNNE_HBsGVXUMe8Ig",
                                               "complete-sector-358111-6507e2db8737.json")
            ai_client = AIResponseGenerator("sk-Hf5sYl71ZmRT9bjwLkQViQ")
            responder = ReviewResponder(ai_client, logger)

            settings = config.get_active_config()
            if not settings['ai_enabled']:
                logger.logger.info(f"[{settings['marketplace']}] Для маркетплейса отключены ответы на отзывы.")
                continue

            api_key = settings.get("api_key")
            if api_key is None:
                raise Exception(f"[{settings['marketplace']}] Не указаны данные API.")#TODO сделать обработку если нет АПИ ключа
            wb_client = WBIntegration(api_key)

            logger.logger.warning(f"[{settings['marketplace']}] Будут отбираться отзывы, имеющие state входящие в {wb_client.state}")

            reviews = wb_client.get_new_reviews(settings['rating_threshold'])

            for raw_review in reviews:
                review = WbReview(**raw_review)
                response = responder.process_review(review, settings['prompt_template'])
                if response:
                    if wb_client.post_response(review['id'], response):
                        logger.logger.info(f"[{review.marketplace}] [{review.id}] Ответ на отзыв успешно отправлен.")
                    else:
                        logger.logger.error(f"[{review.marketplace}] [{review.id}] Произошла ошибка при отправке ответа на отзыв.")


        except Exception as e:
            error_msg = f"Main loop error: {str(e)}\n\n{traceback.format_exc()}"
            logger.logger.error(error_msg)
            notifier.send_alert(f"🚨 Critical Error\n{error_msg}", level="CRITICAL")
        finally:
            time.sleep(60)
if __name__ == '__main__':
    main()