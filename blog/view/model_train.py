import json
import logging
from blog.tasks import train_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

@login_required
def train_view(request):
    return render(request, "blog/model_train.html")

@csrf_exempt
@require_POST
def train_api(request):
    data = json.loads(request.body.decode("utf-8"))
    logger.info(f"收到訓練請求: {data}")

    if data.get("model") != "Mamba":
        return JsonResponse(
            {"status": "error", "message": "❌ 尚未支援該模型架構"},
            status=400 
        )

    task = train_model.delay(
        model=data.get("model"),
        dataset=data.get("dataset"),
        epochs=data.get("epochs"),
        batch_size=data.get("batch_size"),
        learning_rate=data.get("learning_rate"),
        validation_freq=data.get("validation_freq"),
    )

    logger.info(f"已提交 Celery 任務 task_id：{task.id}")

    return JsonResponse({
        "status": "submitted",
        "task_id": task.id,
        "message": f"已提交訓練: 模型={data.get('model')}, 資料集={data.get('dataset')}"
    })