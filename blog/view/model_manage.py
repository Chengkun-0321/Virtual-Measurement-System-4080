import os
import pytz
import json
import subprocess
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods

def manage_models(request):
    return render(request, 'blog/model_manage.html')

# 列出本機模型檔案清單 (GET)
@csrf_exempt
@require_GET
def list_checkpoint(request):
    weights_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/checkpoints")
    try:
        weights = []
        taiwan_tz = pytz.timezone("Asia/Taipei")

        for fname in os.listdir(weights_dir):
            if fname.endswith(".h5"):
                name = fname.replace(".h5", "")
                full_path = os.path.join(weights_dir, fname)
                stat_info = os.stat(full_path)

                dt = datetime.fromtimestamp(stat_info.st_mtime, taiwan_tz)
                mtime = dt.strftime("%Y/%m/%d %H:%M:%S")

                metadata_path = os.path.join(weights_dir, f"{name}.json")
                acc = None
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        acc = metadata.get("acc")

                weights.append({
                    "name": name,
                    "size": f"{stat_info.st_size / (1024 * 1024):.2f} MB",
                    "date": mtime,
                    "acc": acc,
                    "timestamp": stat_info.st_mtime
                })

        # 排序
        sort_by = request.GET.get("sort_by")
        order = request.GET.get("order", "desc")

        if sort_by == "acc":
            weights.sort(key=lambda x: (x["acc"] is None, x["acc"]), reverse=(order == "desc"))
        elif sort_by == "date":
            weights.sort(key=lambda x: x["timestamp"], reverse=(order == "desc"))
        else:
            weights.sort(key=lambda x: x["timestamp"], reverse=True)

        return JsonResponse(weights, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# 刪除本機模型檔案 (POST)
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_checkpoint(request):
    try:
        data = json.loads(request.body)
        filenames = data.get("filenames", [])
        if not filenames:
            return JsonResponse({"status": "error", "error": "未指定要刪除的檔案"})

        base_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code")
        for filename in filenames:
            weight_path = os.path.join(base_dir, "checkpoints", f"{filename}.h5")
            json_path = os.path.join(base_dir, "checkpoints", f"{filename}.json")
            folder_path = os.path.join(base_dir, "Training_History_Plot", filename)

            if os.path.exists(weight_path):
                os.remove(weight_path)
            if os.path.exists(json_path):
                os.remove(json_path)
            if os.path.exists(folder_path):
                subprocess.call(["rm", "-rf", folder_path])

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})


# 重新命名本機模型檔案 (POST)
@csrf_exempt
@require_http_methods(["PUT"])
def rename_checkpoint(request):
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