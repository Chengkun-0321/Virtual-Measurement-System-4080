# blog/__init__.py
default_app_config = "blog.apps.BlogConfig"

# 確保 Celery signals 被載入
from . import celery_signals