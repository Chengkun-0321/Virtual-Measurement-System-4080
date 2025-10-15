import os
import json
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

MODEL_DIR = "/home/vms/Virtual_Measurement_System_model/Model_code/checkpoints/"
IMG_DIR = "/home/vms/Virtual_Measurement_System_model/Model_code/Training_History_Plot"

# 資料分析頁面
@require_GET
def data_analysis(request):
    return render(request, "blog/data_analysis.html")

# 取得模型清單
@csrf_exempt
@require_POST
def list_model_names(request):
    models = [
        f.replace(".h5", "")
        for f in os.listdir(MODEL_DIR)
        if f.endswith(".h5")
    ]
    models.sort()
    return JsonResponse({"models": models})

# 取得圖片 URL (後端幫拼好 API 路徑)
@csrf_exempt
@require_POST
def get_model_images(request):
    body = json.loads(request.body.decode("utf-8"))
    model_name = body.get("model_name")
    if not model_name:
        return JsonResponse({"error": "缺少 model_name"}, status=400)

    image_map = {
        "mape": "training_mape_curve.png",
        "mse": "training_mse_curve.png",
        "loss": "training_loss_curve.png",
        "mae": "training_mae_curve.png",
        "gt": "ground_truth.png"
    }

    result = {}
    for key, filename in image_map.items():
        file_path = os.path.join(IMG_DIR, model_name, filename)
        if os.path.exists(file_path):
            # 後端直接產生 API URL，前端不用再拼
            result[key] = f"/api/get_image/{model_name}/{filename}"
        else:
            result[key] = None

    return JsonResponse({"images": result})

# 單張圖片 (只給 <img> 用)
@require_GET
def get_result_image(request, folder, filename):
    file_path = os.path.join(IMG_DIR, folder, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), content_type="image/png")
    else:
        raise Http404("找不到圖片")

# 下載模型
@csrf_exempt
@require_POST
def download_model(request):
    body = json.loads(request.body.decode("utf-8"))
    model_name = body.get("model_name")
    if not model_name:
        return JsonResponse({"error": "缺少 model_name"}, status=400)

    file_path = os.path.join(MODEL_DIR, f"{model_name}.h5")
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=f"{model_name}.h5")
    else:
        raise Http404("找不到模型檔案")