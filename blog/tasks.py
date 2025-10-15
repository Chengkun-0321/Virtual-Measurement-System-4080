# blog/tasks.py
import os
import logging
import subprocess
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model

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
        f"--train_x './process_data_Splitting/training_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
        f"--train_y './process_data_Splitting/training_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
        f"--valid_x './process_data_Splitting/validation_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
        f"--valid_y './process_data_Splitting/validation_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
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
        logger.info(f"將訊息送到前端 TRAIN/: {log_line}")

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
        f"--test_x_path './process_data_Splitting/testing_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
        f"--test_y_path './process_data_Splitting/testing_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
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
        logger.info(f"將訊息送到前端 TEST/: {log_line}")

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
    Celery 任務：呼叫模型做預測
    """
    channel_layer = get_channel_layer()
    logs = []
    try:
        # 還原 DataFrame
        selected_df = pd.read_json(data_json, orient="split")

        # 模型路徑
        model_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code/checkpoints")
        model_path = os.path.join(model_dir, model_name + ".h5")

        # 載入模型
        msg = f"📂 載入模型 {model_name}.h5"
        async_to_sync(channel_layer.group_send)(
            "deploying_group",
            {"type": "deploying.log", "message": msg}
        )
        logger.info(msg)
        model = load_model(model_path, compile=False)

        # 預測資料
        data_np = selected_df.to_numpy().reshape(-1, 9, 9, 1).astype(np.float32)
        msg = f"▶️ 開始預測，共 {data_np.shape[0]} 筆資料"
        async_to_sync(channel_layer.group_send)(
            "deploying_group",
            {"type": "deploying.log", "message": msg}
        )
        logger.info(msg)

        predictions = model.predict(data_np, verbose=1)

        for i, value in enumerate(predictions.flatten().round(3).tolist()):
            log_line = f"[{i+1}] {value}"
            logs.append(log_line)
            async_to_sync(channel_layer.group_send)(
                "deploying_group",
                {"type": "deploying.log", "message": log_line}
            )
            logger.info(f"將訊息送到前端 DEPLOY/:{log_line}")
        
        pred_result = predictions.flatten().round(3).tolist()

        # 預測完成通知
        async_to_sync(channel_layer.group_send)(
            "deploying_group",
            {"type": "deploying.log", "message": f"✅ 完成預測，共 {len(pred_result)} 筆"}
        )

            # 傳送預測結果
        async_to_sync(channel_layer.group_send)(
            "deploying_group",
            {"type": "deploying.log", "message": f"結果: {pred_result}"}
        )

        return {"status": "success", "predictions": pred_result}

    except Exception as e:
        async_to_sync(channel_layer.group_send)(
            "deploying_group",
            {"type": "deploying.log", "message": f"❌ Error: {str(e)}"}
        )
        return {"status": "error", "message": str(e)}