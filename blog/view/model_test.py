import os, json
import logging
from blog.tasks import test_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404, FileResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

logger = logging.getLogger(__name__)
MODEL_DIR = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/checkpoints")
IMG_DIR = "/home/vms/Virtual_Measurement_System_model/Model_code/Training_History_Plot"

@login_required
def test_view(request):
    return render(request, "blog/model_test.html")

@csrf_exempt
@require_POST
def test_api(request):
    data = json.loads(request.body.decode("utf-8"))
    logger.info(f"收到測試請求: {data}")

    if data.get("model") != "Mamba":
        return JsonResponse(
            {"status": "error", "message": "❌ 尚未支援該模型架構"},
            status=400 
        )
    
    task = test_model.delay(
        model = data.get("model"),
        dataset = data.get("dataset"),
        checkpoint = data.get("checkpoint_path"),
        mean = data.get("mean"),
        upper = data.get("boundary_upper"),
        lower = data.get("boundary_lower"),
    )

    logger.info(f"已提交 Celery 任務 task_id：{task.id}")

    
    return JsonResponse({
        "status": "submitted",
        "task_id": task.id,
        "message": f"已提交測試: 模型={data.get('model')}, 資料集={data.get('dataset')}, checkpoint={data.get('checkpoint')}"
    })

@require_GET
def test_list_checkpoints(request):
    """回傳 checkpoints 底下的所有 .h5 權重檔。

    改為使用 GET：用戶端可以直接以瀏覽器或 AJAX 的 GET 請求取得清單。
    """
    try:
        checkpoints = [
            f.replace(".h5", "") for f in os.listdir(MODEL_DIR) if f.endswith(".h5")
        ]
    except FileNotFoundError:
        checkpoints = []

    checkpoints.sort()
    return JsonResponse({"checkpoints": checkpoints})

@csrf_exempt
@require_POST
def post_test_images(request):
    """測試完成後回傳圖片 URL"""
    data = json.loads(request.body.decode("utf-8"))
    model_name = data.get("model_name", "default")
    return JsonResponse({
        "images": {
            "mape": f"/api/get_test_image/{model_name}/混淆矩陣.png",
            "ground_truth": f"/api/get_test_image/{model_name}/ground_truth.png"
        }
    })