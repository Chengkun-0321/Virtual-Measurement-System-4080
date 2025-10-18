import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

app = Celery("mysite")

app.conf.update(
    broker_url = "amqp://guest:guest@localhost:5672//",  # RabbitMQ 當 broker
    result_backend = "redis://127.0.0.1:6379/0",         # Redis 存結果
    task_serializer = 'json',
    result_serializer = 'json',
    accept_content = ['json'],
    timezone = 'Asia/Taipei',
    enable_utc = True,
)

# 自動發現 tasks.py
app.autodiscover_tasks()