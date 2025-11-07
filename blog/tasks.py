# blog/tasks.py
import json
import os
import logging
import subprocess
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def train_model(self, model, dataset, epochs, batch_size, learning_rate, validation_freq):
    """
    Celery 任務：呼叫 mamba 環境的 train_code.py 執行模型訓練
    """
    if model == "Mamba":
        model_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/")
        venv_dir = "mamba"
        py_file = "train_code.py"
    else:
        return {"status": "error", "logs": ["❌ 尚未支援該模型架構"]}

    cmd = (
        f"cd {model_dir} && "
        f"source ~/anaconda3/etc/profile.d/conda.sh && "
        f"conda activate {venv_dir} && "
        f"python {py_file} "
        f"--train_x './Dataset/{dataset}/Train/x.npy' "
        f"--train_y './Dataset/{dataset}/Train/y.npy' "
        f"--valid_x './Dataset/{dataset}/Validation/x.npy' "
        f"--valid_y './Dataset/{dataset}/Validation/y.npy' "
        f"--epochs {epochs} --batch_size {batch_size} --lr {learning_rate} --validation_freq {validation_freq}"
    )

    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable="/bin/bash"
    )

    # 準備 WebSocket channel layer
    channel_layer = get_channel_layer()

    logs = []
    for line in iter(process.stdout.readline, b""):
        log_line = line.decode().strip()
        logs.append(log_line)

        # 即時推送到 WebSocket (training_group 是你在 consumer 裡訂的 group name)
        async_to_sync(channel_layer.group_send)(
            "training_group",
            {
                "type": "training.log",   # 會呼叫 consumer 裡的 training_log()
                "message": log_line
            }
        )
        logger.info(f"將訊息透過 redis 送到前端 TRAIN/: {log_line}")

    process.wait()
    err = process.stderr.read().decode()
    if err:
        logs.append("❌ Error: " + err)
        async_to_sync(channel_layer.group_send)(
            "training_group",
            {"type": "training.log", "message": "❌ Error: " + err}
        )

    # 訓練完成通知
    async_to_sync(channel_layer.group_send)(
        "training_group",
        {"type": "training.log", "message": "__FINISHED__"}
    )

    return {"status": "done"}

@shared_task(bind=True)
def test_model(self, model, dataset, checkpoint, mean, upper, lower):
    """
    Celery 任務：呼叫 mamba 環境的 test_code.py 執行模型訓練
    """
    if model == "Mamba":
        model_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/")
        venv_dir = "mamba"
        py_file = "test_code.py"
    else:
        return {"status": "error", "logs": ["❌ 尚未支援該模型架構"]}

    cmd = (
        f"cd {model_dir} && "
        f"source ~/anaconda3/etc/profile.d/conda.sh && "
        f"conda activate {venv_dir} && "
        f"python -u {py_file} "
        f"--test_x_path './Dataset/{dataset}/Test/x.npy' "
        f"--test_y_path './Dataset/{dataset}/Test/y.npy' "
        f"--checkpoint_path checkpoints/{checkpoint}.h5 "
        f"--mean '{mean}' "
        f"--boundary_upper '{upper}' "
        f"--boundary_lower '{lower}'"
    )

    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable="/bin/bash"
    )

    # 準備 WebSocket channel layer
    channel_layer = get_channel_layer()

    logs = []
    for line in iter(process.stdout.readline, b""):
        log_line = line.decode().strip()
        logs.append(log_line)

        # 即時推送到 WebSocket (training_group 是你在 consumer 裡訂的 group name)
        async_to_sync(channel_layer.group_send)(
            "testing_group",
            {
                "type": "testing.log",   # 會呼叫 consumer 裡的 testing_log()
                "message": log_line
            }
        )
        logger.info(f"將訊息透過 redis 送到前端 TEST/: {log_line}")

    process.wait()
    err = process.stderr.read().decode()
    if err:
        logs.append("❌ Error: " + err)
        async_to_sync(channel_layer.group_send)(
            "testing_group",
            {"type": "testing.log", "message": "❌ Error: " + err}
        )

    # 訓練完成通知
    async_to_sync(channel_layer.group_send)(
        "testing_group",
        {"type": "testing.log", "message": "__FINISHED__"}
    )

    return {"status": "done"}

@shared_task(bind=True)
def predict_model(self, model_name, indices, data_json):
    """
    Celery 任務：呼叫 mamba 環境的 predict_code.py 做預測
    """
    # 1. WebSocket 群組 (對應前端 DEPLOY)
    channel_layer = get_channel_layer()

    # 2. 檔案與環境設定
    model_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/")
    venv_dir = "mamba"
    py_file = "predict_code.py"
    data_path = os.path.join(model_dir, "predict.json")

    # 3. 儲存 data_json 到 predict.json（需轉成 dict 才能正確 dump）
    print(f"👉 寫入 JSON 到: {data_path}")
    if isinstance(data_json, str):
        data_json = json.loads(data_json)

    with open(data_path, "w") as f:
        json.dump(data_json, f)

    # 4. 建立執行指令（不阻塞 Django）
    cmd = (
        f"cd {model_dir} && "
        f"source ~/anaconda3/etc/profile.d/conda.sh && "
        f"conda activate {venv_dir} && "
        f"python -u {py_file} "
        f"--model {model_name} "      # 這裡 model_name 不用加 .h5
    )
    print(f"🚀 執行指令：{cmd}")

    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable="/bin/bash"
    )

    # 5. 即時讀取 stdout
    logs = []
    predictions = []
    for line in iter(process.stdout.readline, b""):
        log_line = line.decode().strip()
        logs.append(log_line)

        # 即時傳給前端
        async_to_sync(channel_layer.group_send)(
            "deploying_group",          # ✅ 對應前端 /ws/DEPLOY/
            {
                "type": "deploying.log",
                "message": log_line
            }
        )

        # 如果抓到 RESULT:[...]
        if log_line.startswith("RESULT:"):
            try:
                predictions = eval(log_line.replace("RESULT:", "").strip())
            except:
                predictions = []

    # 6. 如果 stderr 有錯誤也推給前端
    err = process.stderr.read().decode()
    if err:
        async_to_sync(channel_layer.group_send)(
            "deploying_group",
            {"type": "deploying.log", "message": "❌ Error: " + err}
        )

    # 7. 通知完成
    async_to_sync(channel_layer.group_send)(
        "deploying_group",
        {"type": "deploying.log", "message": "__FINISHED__"}
    )

    return {"status": "done", "predictions": predictions}