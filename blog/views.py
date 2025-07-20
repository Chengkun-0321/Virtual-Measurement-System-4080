import os
import re
import time
import json
import subprocess
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime

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
@csrf_exempt
def run_mamba_local(request):
    if request.method == "POST":
        model = request.POST['model']
        dataset = request.POST['dataset']

        if model == "Mamba":
            model_dir = os.path.expanduser("~/Virtual_Measurement_System_model/HMamba_code")
            venv_dir = "mamba"
            py_file = "HMambaTrain_ov.py"
        else:
            return render(request, 'blog/model_train.html', {'output': "❌ 無效的模型選擇"})

        output = execute_train_command(model_dir, venv_dir, py_file, dataset)
        return render(request, 'blog/model_train.html', {'output': output})
    return render(request, 'blog/model_train.html')

# 執行訓練指令是設定
def execute_train_command(model_dir, venv_dir, py_file, dataset):
    cmd = (
        f"cd {model_dir} && "
        f"source ~/anaconda3/etc/profile.d/conda.sh && "
        f"conda activate {venv_dir} && "
        f"python {py_file} "
        f"--train_x './training_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
        f"--train_y './training_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
        f"--valid_x './validation_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
        f"--valid_y './validation_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
        "--epochs 2 --batch_size 129 --lr 0.0001 --validation_freq 100"
    )

    # 執行指令並回傳輸出
    result = subprocess.run(cmd, shell=True, executable="/bin/bash", capture_output=True, text=True)
    return result.stdout + result.stderr


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
        for fname in os.listdir(weights_dir):
            if fname.endswith(".h5"):
                # 回傳 json 格式調整
                full_path = os.path.join(weights_dir, fname)
                stat_info = os.stat(full_path)
                file_size = f"{stat_info.st_size / (1024 * 1024):.2f} MB"
                mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y/%m/%d %H:%M:%S")
                mse_match = re.search(r"valmse_([\d.]+)", fname)
                mse = float(mse_match.group(1).rstrip('.')) if mse_match else None

                weights.append({
                    "name": fname.replace(".h5", ""),
                    "size": file_size,
                    "date": mtime,
                    "mse": mse
                })

        weights.sort(key=lambda x: x['date'], reverse=True)
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
            
            old_folder = os.path.join(base_dir, "Training_History_Plot", old_name)
            new_folder = os.path.join(base_dir, "Training_History_Plot", new_name)
            if os.path.exists(old_folder):
                os.rename(old_folder, new_folder)

            os.rename(old_path, new_path)
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)})

    return JsonResponse({"status": "error", "error": "無效的請求"})


# ----- 資料下載畫面 -----
def data_download(request):
    return render(request, 'blog/data_download.html')