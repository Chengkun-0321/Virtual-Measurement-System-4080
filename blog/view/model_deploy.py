import os
import json
import logging
import numpy as np
import pandas as pd
from blog.tasks import predict_model
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

logger = logging.getLogger(__name__)
model_dir = "/home/vms/Virtual_Measurement_System_model/Model_code/checkpoints/"
uploaded_data = None  # 全域暫存匯入資料

@login_required
def model_deploy(request):
    return render(request, "blog/model_deploy.html")

@require_GET
def deploy_list_checkpoints(request):
    """列出可用的模型檔名"""
    model_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/checkpoints")
    models = [f.replace(".h5", "") for f in os.listdir(model_dir) if f.endswith(".h5")]
    models.sort()
    return JsonResponse({"models": models})

# csv 版本
"""
def download_random_100(request):
    # CSV 檔案路徑
    csv_path = os.path.join(settings.BASE_DIR, 'static', 'test-data.csv')

    # 讀取 CSV
    df = pd.read_csv(csv_path)

    # 隨機抽取 100 筆
    sampled_df = df.sample(n=100, random_state=random.randint(0, 9999))

    # 轉換為 CSV 格式（存成記憶體中的檔案）
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sampled_100.csv"'
    sampled_df.to_csv(path_or_buf=response, index=False)

    return response
"""

# npy 版本
def download_random_100(request):
    # npy 檔案路徑（這是已經轉好的 (N, 9, 9)）
    npy_path = os.path.join(settings.BASE_DIR, 'static', 'data/test-data.npy')

    # 載入 npy 資料
    full_data = np.load(npy_path)

    # 隨機抽取 100 筆資料
    sampled_indices = np.random.choice(full_data.shape[0], 100, replace=False)
    sampled_data = full_data[sampled_indices]

    # 將資料存成 Bytes 格式放進 HttpResponse
    response = HttpResponse(content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename="sampled_100.npy"'
    np.save(response, sampled_data)

    return response


@csrf_exempt
@require_POST
def import_data(request):
    global uploaded_data  # ← 必加
    if request.method == 'POST' and request.FILES.get('file'):
        npy_file = request.FILES['file']
        
        # 載入 npy 檔
        data = np.load(npy_file, allow_pickle=True)  # (N, 9, 9)
        if len(data.shape) == 3 and data.shape[1:] == (9, 9):
            num_samples = data.shape[0]

            # 儲存為 DataFrame，讓 predict 也能取用（展平）
            flat_data = data.reshape(num_samples, -1)
            uploaded_data = pd.DataFrame(flat_data)

            # 回傳前端預覽欄位
            columns = [f'F{i}' for i in range(flat_data.shape[1])]
            rows = flat_data.tolist()

            return JsonResponse({
                'columns': columns,
                'rows': rows
            })
        return JsonResponse({'error': '格式錯誤，請上傳 shape 為 (N, 9, 9) 的 .npy 檔案'}, status=400)
    return JsonResponse({'error': '請使用 POST 並上傳檔案'}, status=400)

'''
@csrf_exempt
@require_POST
def predict_api(request):
    global uploaded_data
    try:
        data = json.loads(request.body.decode("utf-8"))
        logger.info(f"收到測試請求: {data}")
        indices = data.get('indices', [])
        model_name = data.get('model')

        if uploaded_data is None:
            return JsonResponse({"error": "尚未上傳資料"}, status=400)
        if not indices:
            return JsonResponse({"error": "未勾選任何資料列"}, status=400)

        selected_df = uploaded_data.iloc[indices]
        model_path = os.path.join(model_dir, model_name + ".h5")

        if not os.path.exists(model_path):
            return JsonResponse({"error": "模型不存在"}, status=404)

        model = load_model(model_path, compile=False)
        data_np = selected_df.to_numpy().reshape(-1, 9, 9, 1).astype(np.float32)
        predictions = model.predict(data_np)
        pred_result = predictions.flatten().round(3).tolist()

        return JsonResponse({"predictions": pred_result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
'''

@csrf_exempt
@require_POST
def predict_api(request):
    global uploaded_data
    try:
        data = json.loads(request.body.decode("utf-8"))
        logger.info(f"收到預測請求: {data}")
        indices = data.get('indices', [])

        if uploaded_data is None:
            return JsonResponse({"error": "尚未上傳資料"}, status=400)
        if not indices:
            return JsonResponse({"error": "未勾選任何資料列"}, status=400)

        model_name = data.get('model')
        selected_df = uploaded_data.iloc[indices]
        data_json = selected_df.to_json(orient="split")

        # 呼叫 Celery
        task = predict_model.delay(model_name, indices, data_json)

        return JsonResponse({
            "status": "submitted",
            "task_id": task.id,
            "message": "預測任務已提交"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)