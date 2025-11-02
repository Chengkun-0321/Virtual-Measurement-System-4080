# blog/celery_signals.py
import requests
from celery import signals
import logging

logger = logging.getLogger(__name__)

API_URL = "http://140.137.41.136:7780//api/tasks/"    # 這裡換成你的實際網址

@signals.task_prerun.connect
def task_started_handler(sender=None, task_id=None, task=None, **kwargs):
    logger.info(f"🚀 任務開始: {task.name} (id={task_id})")
    try:
        requests.get(API_URL, timeout=5)   # 任務開始時打 API
    except Exception as e:
        logger.error(f"任務開始 API 呼叫失敗: {e}")

@signals.task_success.connect
def task_success_handler(sender=None, result=None, task_id=None, **kwargs):
    logger.info(f"✅ 任務完成: {sender.name} (id={task_id})")
    try:
        requests.get(API_URL, timeout=5)   # 任務完成時打 API
    except Exception as e:
        logger.error(f"任務完成 API 呼叫失敗: {e}")

@signals.task_failure.connect
def task_failure_handler(sender=None, exception=None, task_id=None, **kwargs):
    logger.info(f"❌ 任務失敗: {sender.name} (id={task_id}) - {exception}")
    try:
        requests.get(API_URL, timeout=5)   # 任務失敗時打 API
    except Exception as e:
        logger.error(f"任務失敗 API 呼叫失敗: {e}")