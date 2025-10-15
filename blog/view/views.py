from django.http import JsonResponse
from celery.result import AsyncResult
from mysite.celery import app

# 查 Celery 任務狀態的 API
def task_status(request, task_id):
    res = AsyncResult(task_id, app=app)
    return JsonResponse({
        "task_id": task_id,
        "status": res.status,
        "result": res.result if res.ready() else None
    })