import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

app = Celery("mysite")

# 使用 RabbitMQ 作為 broker
app.conf.broker_url = "amqp://guest:guest@localhost:5672//"

# 如果要存結果，可以加上 backend，例如 Redis 或 Django-DB
app.conf.result_backend = "rpc://"

# 自動發現 tasks.py
app.autodiscover_tasks()