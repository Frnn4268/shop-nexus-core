from celery import Celery
import time
import os

celery = Celery(__name__)
celery.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND"),
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
        # Simular envío
        time.sleep(2)
        print(f"📧 Email enviado a {email}: {subject} - {message}")
        return True
    except Exception as e:
        self.retry(exc=e, countdown=30)

@celery.task(bind=True, max_retries=3)
def send_sms(self, phone, message):
    try:
        # Simular envío
        time.sleep(1)
        print(f"📱 SMS enviado a {phone}: {message}")
        return True
    except Exception as e:
        self.retry(exc=e, countdown=15)