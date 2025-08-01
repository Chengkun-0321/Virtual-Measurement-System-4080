import os
import re
import time
import pytz
import json
import subprocess
import zipfile
from io import BytesIO
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils.timezone import localtime
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model

# 首頁畫面
@csrf_exempt
def home(request):
    # 透過 mysite/setting.py TEMPLATES = [....] 自動尋找 blog/home.html 顯示首頁
    if request.method == "POST":
        # 存進 session
        request.session['hostname'] = request.POST.get('hostname', '')
        request.session['port'] = request.POST.get('port', '')
        request.session['username'] = request.POST.get('username', '')
        request.session['password'] = request.POST.get('password', '')
        return render(request, 'home.html')

    # 讀取 session 並傳到 template
    context = {
        'hostname': request.session.get('hostname', ''),
        'port': request.session.get('port', ''),
        'username': request.session.get('username', ''),
        'password': request.session.get('password', '')
    }
    return render(request, 'blog/home.html', context)  

def ping_test(request):
    if request.method == 'POST':
        # 取得 port 並檢查格式是否正確（必須是數字）
        port_str = request.POST.get('port')
        if not port_str or not port_str.isdigit():
            # 如果 port 沒有填或不是數字，回傳錯誤訊息
            return JsonResponse({'status': 'error', 'message': '⚠️ 請輸入有效的 Port 號碼'})

        # 取得其他 SSH 連線資訊（hostname、username、password）
        hostname = request.POST.get('hostname')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 將這些 SSH 資訊暫存到 Django session（給其他頁面用）
        request.session['ssh_info'] = {
            'hostname': hostname,
            'port': port_str,
            'username': username,
            'password': password
        }

        # 建立 SSH 連線測試
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(hostname=hostname, port=int(port_str), username=username, password=password)
            ssh.close()
            return JsonResponse({'status': 'success', 'message': '✅ 成功連線！'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'❌ 連線失敗：{str(e)}'})

# ----- 訓練模型頁面 -----
def run_mamba_local(request):
    return render(request, 'blog/model_train.html')

# ----- 測試模型畫面 -----
def test_model(request):
    # 掃描 checkpoints 資料夾取得權重名稱
    weights_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/checkpoints")
    try:
        checkpoint_folders = [
            f.replace(".h5", "") for f in os.listdir(weights_dir) if f.endswith(".h5")
        ]
    except FileNotFoundError:
        checkpoint_folders = []

    return render(request, 'blog/model_test.html', {'checkpoint_folders': checkpoint_folders})

# 取得測試結果圖片
def get_result_image(request, folder, filename):
    base_dir = "/home/vms/Virtual_Measurement_System_model/Model_code/Training_History_Plot"
    file_path = os.path.join(base_dir, folder, filename)
    print("請求圖片路徑:", file_path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), content_type="image/png")
    return JsonResponse({"error": "找不到圖片"}, status=404)

# ----- 模型管理畫面 -----
def manage_models(request):
    return render(request, 'blog/model_manage.html')

# 列出本機模型檔案清單
def list_checkpoint(request):
    weights_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/checkpoints")
    try:
        weights = []
        taiwan_tz = pytz.timezone("Asia/Taipei")  # 台灣時區轉換

        for fname in os.listdir(weights_dir):
            if fname.endswith(".h5"):
                name = fname.replace(".h5", "")
                full_path = os.path.join(weights_dir, fname)
                stat_info = os.stat(full_path)
                file_size = f"{stat_info.st_size / (1024 * 1024):.2f} MB"

                dt = datetime.fromtimestamp(stat_info.st_mtime, taiwan_tz)
                mtime = dt.strftime("%Y/%m/%d %H:%M:%S")  # 給畫面看的
                mtime_iso = dt.strftime("%Y-%m-%d")       # 給篩選用

                metadata_path = os.path.join(weights_dir, f"{name}.json")
                mse = None
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        mse = metadata.get("mse")

                weights.append({
                    "name": name,
                    "size": f"{stat_info.st_size / (1024 * 1024):.2f} MB",
                    "date": mtime,
                    "mse": mse,
                    "timestamp": stat_info.st_mtime
                })

        # 讀取排序參數
        sort_by = request.GET.get("sort_by")  # mse 或 date
        order = request.GET.get("order", "desc")  # asc 或 desc

        if sort_by == "mse":
            weights.sort(key=lambda x: (x['mse'] is None, x['mse']), reverse=(order == "desc"))
        elif sort_by == "date":
            weights.sort(key=lambda x: x['timestamp'], reverse=(order == "desc"))
        else:
            weights.sort(key=lambda x: x['timestamp'], reverse=True)  # 預設照時間新到舊

        return JsonResponse(weights, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    
# 刪除本機模型檔案與資料夾
@csrf_exempt
def delete_local_weights(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            filenames = data.get("filenames", [])

            if not filenames:
                return JsonResponse({"status": "error", "error": "未指定要刪除的檔案"})

            base_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code")
            for filename in filenames:
                weight_path = os.path.join(base_dir, "checkpoints", f"{filename}.h5")
                folder_path = os.path.join(base_dir, "Training_History_Plot", filename)

                if os.path.exists(weight_path):
                    os.remove(weight_path)
                if os.path.exists(folder_path):
                    subprocess.call(["rm", "-rf", folder_path])

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)})

    return JsonResponse({"status": "error", "error": "無效的請求"})

# 重新命名本機模型檔案
@csrf_exempt
def rename_checkpoint(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            old_name = data.get("old_name")
            new_name = data.get("new_name")

            if not old_name or not new_name:
                return JsonResponse({"status": "error", "error": "缺少必要參數"})

            base_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code")
            old_path = os.path.join(base_dir, "checkpoints", f"{old_name}.h5")
            new_path = os.path.join(base_dir, "checkpoints", f"{new_name}.h5")

            if not os.path.exists(old_path):
                return JsonResponse({"status": "error", "error": "原始檔案不存在"})
            if os.path.exists(new_path):
                return JsonResponse({"status": "error", "error": "新檔案名稱已存在"})

            # 同步資料夾改名
            old_folder = os.path.join(base_dir, "Training_History_Plot", old_name)
            new_folder = os.path.join(base_dir, "Training_History_Plot", new_name)
            if os.path.exists(old_folder):
                os.rename(old_folder, new_folder)

            # 同步 JSON metadata 改名
            old_json = os.path.join(base_dir, "checkpoints", f"{old_name}.json")
            new_json = os.path.join(base_dir, "checkpoints", f"{new_name}.json")
            if os.path.exists(old_json):
                os.rename(old_json, new_json)

            # 改名 .h5
            os.rename(old_path, new_path)

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)})

    return JsonResponse({"status": "error", "error": "無效的請求"})

# ----- 部署模型畫面 -----
def deploy_model(request):
    return render(request, "blog/deploy_model.html")

uploaded_data = None  # 全域暫存匯入資料

@csrf_exempt
def upload_csv(request):
    global uploaded_data
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            file = request.FILES['file']
            df = pd.read_csv(file)
            uploaded_data = df
            preview = df.head(20).values.tolist()
            return JsonResponse({
                "columns": list(df.columns),
                "rows": preview
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "請提供CSV檔"}, status=400)

@csrf_exempt
def predict_from_selected_rows(request):
    global uploaded_data
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            indices = body.get('indices', [])
            model_name = body.get('model')

            if uploaded_data is None:
                return JsonResponse({"error": "尚未上傳資料"}, status=400)

            selected_df = uploaded_data.iloc[indices]
            model_path = os.path.join(model_dir, model_name + ".h5")

            if not os.path.exists(model_path):
                return JsonResponse({"error": "模型不存在"}, status=404)

            model = load_model(model_path)
            predictions = model.predict(selected_df.to_numpy())
            pred_result = predictions.flatten().round(3).tolist()

            return JsonResponse({"predictions": pred_result})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "無效請求"}, status=400)

# ----- 資料分析畫面 -----
# 模型和圖像資料夾
model_dir = "/home/vms/Virtual_Measurement_System_model/Model_code/checkpoints/"

@require_GET
def list_model_names(request):
    try:
        models = [
            f.replace(".h5", "")
            for f in os.listdir(model_dir)
            if f.endswith(".h5")
        ]
        models.sort()
        return JsonResponse({"models": models})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def data_analysis(request):
    return render(request, 'blog/data_analysis.html')

def download_file(request, file_type, model_name):
    base_path = "/home/vms/Virtual_Measurement_System_model/Model_code"

    # 對應不同檔案類型的子路徑
    file_map = {
        "model": f"checkpoints/{model_name}.h5",
        "confusion": f"Training_History_Plot/{model_name}/混淆矩陣.png",
        "ground_truth": f"Training_History_Plot/{model_name}/ground_truth.png",
        "loss": f"Training_History_Plot/{model_name}/training_loss_curve.png",
        "mae": f"Training_History_Plot/{model_name}/training_mae_curve.png",
        "mape": f"Training_History_Plot/{model_name}/training_mape_curve.png",
        "mse": f"Training_History_Plot/{model_name}/training_mse_curve.png"
    }

    rel_path = file_map.get(file_type)
    if not rel_path:
        raise Http404("檔案類型無效")

    file_path = os.path.join(base_path, rel_path)

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    else:
        raise Http404("找不到檔案")