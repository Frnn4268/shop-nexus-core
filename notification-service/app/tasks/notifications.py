import logging
import time

from celery import Celery

from app.core.config import settings
from app.core.logging_config import configure_logging


LOGGER = logging.getLogger(__name__)
configure_logging()

celery = Celery(__name__)
celery.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=100,
    task_create_missing_queues=True,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    worker_send_task_events=True
)

@celery.task(bind=True, max_retries=3)
def send_email(self, email, subject, message):
    try:
        time.sleep(2)
        LOGGER.info("Email notification sent to %s with subject %s", email, subject)
        return True
    except Exception as e:
        self.retry(exc=e, countdown=30)

@celery.task(bind=True, max_retries=3)
def send_sms(self, phone, message):
    try:
        time.sleep(1)
        LOGGER.info("SMS notification sent to %s", phone)
        return True
    except Exception as e:
        self.retry(exc=e, countdown=15)