import time
import traceback

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
                                               "complete-sector-358111-6507e2db8737.json",
                                               logger)
            settings = config.get_active_config()
            for market in settings:
                if market["marketplace"] != "WB":
                    continue
                if not market['ai_enabled']:
                    logger.logger.info(f"[{market['account']}] [{market['marketplace']}] Для маркетплейса отключены ответы на отзывы.")
                    continue
                if not market['ai_key']:
                    raise Exception(f"[{market['account']}] [{market['marketplace']}] Не указан ключ от ИИ.")

                ai_client = AIResponseGenerator(market['ai_key'])
                responder = ReviewResponder(market['account'], ai_client, logger)

                m_api_key = market.get("api_key") #TODO когда сделаю Озон нужно добавить еще API Login
                if m_api_key is None:
                    raise Exception(f"[{market['account']}] [{market['marketplace']}] Не указаны данные API.")
                wb_client = WBIntegration(m_api_key)

                logger.logger.warning(f"[{market['account']}] [{market['marketplace']}] Будут отбираться отзывы, имеющие state входящие в {wb_client.state}")

                reviews = wb_client.get_new_reviews(market['rating_threshold'])
                reviews += wb_client.get_new_reviews(market['rating_threshold'], is_answered=True)

                logger.logger.info(f"[{market['account']}] [{market['marketplace']}] Получено {len(reviews)} неотвеченных отзывов")

                for raw_review in reviews:
                    review = WbReview(**raw_review)
                    base_prompt = market['prompt_options'].get('Обязательная часть', '')
                    prompt = market['prompt_options'].get(market['prompt_template'], '')
                    response = responder.process_review(review, base_prompt, prompt)
                    if response:
                        if wb_client.post_response(review.id, response):
                            logger.logger.info(f"[{market['account']}] [{review.marketplace}] [{review.id}] Ответ на отзыв успешно отправлен.")
                        else:
                            logger.logger.error(f"[{market['account']}] [{review.marketplace}] [{review.id}] Произошла ошибка при отправке ответа на отзыв.")


        except Exception as e:
            error_msg = f"Main loop error: {str(e)}\n\n{traceback.format_exc()}"
            error_msg_tlg = f"Main loop error: {str(e)}\n\n"
            logger.logger.error(error_msg)
            notifier.send_alert(f"🚨 Critical Error\n{error_msg_tlg}", level="CRITICAL")
        finally:
            time.sleep(60)
if __name__ == '__main__':
    main()