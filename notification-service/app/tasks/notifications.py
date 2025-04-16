from celery import Celery
import time
import os

celery = Celery(
    'tasks',
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    broker_connection_retry_on_startup=True,  
    broker_connection_max_retries=10
)

@celery.task
def send_email(email: str, message: str):
    # Simular envío de email
    time.sleep(3)
    print(f"📧 Email enviado a {email}: {message}")
    return True

@celery.task
def send_sms(phone: str, message: str):
    # Simular envío de SMS
    time.sleep(2)
    print(f"📱 SMS enviado a {phone}: {message}")
    return True