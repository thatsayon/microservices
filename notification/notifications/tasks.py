from celery import shared_task
from .sio import sio
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_notification_task(self, data, user_id):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                sio.emit("new_notification", data, room=f"user_{user_id}")
            )
            logger.info(f"Notification sent to user {user_id}")
        finally:
            loop.close()
    except Exception as exc:
        logger.error(f"Failed to send notification: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
