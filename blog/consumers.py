import asyncio
import json
import logging
import os
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class CMDConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        self.send(text_data=json.dumps({"message": "Received!"}))

        if action == 'run-test':
            await self.send(text_data="✅ 後端收到 run-test 指令")
            await self.send("📡 本機執行測試中...")
            model = data['model']
            dataset = data['dataset']
            checkpoint_path = data['checkpoint_path']
            mean = data['mean']
            upper = data['boundary_upper']
            lower = data['boundary_lower']

            model_dir = os.path.expanduser("~/Virtual_Measurement_System_model/Model_code")
            py_file = "test_code.py"
            venv_dir = "mamba"

            cmd = (
                f"cd {model_dir} && "
                f"source ~/anaconda3/etc/profile.d/conda.sh && "
                f"conda activate {venv_dir} && "
                f"python -u {py_file} "
                f"--test_x_path './process_data_Splitting/testing_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
                f"--test_y_path './process_data_Splitting/testing_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
                f"--checkpoint_path checkpoints/{checkpoint_path}.h5 "
                f"--mean '{mean}' "
                f"--boundary_upper '{upper}' "
                f"--boundary_lower '{lower}'"
            )
            await self.run_command(cmd)

        elif action == 'list-models':
            # 取得模型檔案列表
            checkpoint_dir = "/home/vms/Virtual_Measurement_System_model/Model_code/checkpoints/"
            cmd = f"ls {checkpoint_dir}"

            try:
                stdin, stdout, stderr = self.ssh.exec_command(cmd)
                files = stdout.read().decode().splitlines()
                error = stderr.read().decode()

                if error:
                    await self.send(json.dumps({
                        "type": "model_list",
                        "status": "error",
                        "message": error
                    }))
                else:
                    model_files = [f for f in files if f.endswith(".pt") or f.endswith(".pth")]
                    await self.send(json.dumps({
                        "type": "model_list",
                        "status": "success",
                        "files": model_files
                    }))
            except Exception as e:
                await self.send(json.dumps({
                    "type": "model_list",
                    "status": "error",
                    "message": str(e)
                }))

        elif action == 'list-heatmap-files':
            folder = data.get("folder")
            print(f"🧪 收到 list-heatmap-files 請求，資料夾：{folder}")
            await self.send_heatmap_filenames(folder)
            
        elif action == 'list-results':
            await self.send_all_result_folders()

    async def run_command(self, cmd):
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            executable="/bin/bash"
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            await self.send(line.decode().rstrip())

        err = await process.stderr.read()
        if err:
            await self.send(f"❌ {err.decode().strip()}")
            
        print(f"執行指令：{cmd}")
    

    async def send_all_result_folders(self):
        heatmaps_dir = 'static/heatmaps'
        trainplot_dir = 'static/trainplot'

        folders = []
        # 以排序後的名稱列出所有資料夾
        for name in sorted(os.listdir(heatmaps_dir)):
            heat_path = os.path.join(heatmaps_dir, name)
            train_path = os.path.join(trainplot_dir, name)

            if os.path.isdir(heat_path) or os.path.isdir(train_path):
                heatmap_url = f"/static/heatmaps/{name}/" if os.path.isdir(heat_path) else None
                trainplot_url = f"/static/trainplot/{name}/" if os.path.isdir(train_path) else None
                folders.append({
                    "date": name,
                    "heatmap_url": heatmap_url,
                    "trainplot_url": trainplot_url
                })

        await self.send(text_data=json.dumps({
            "type": "media_folders",
            "folders": folders
        }))


    async def send_heatmap_filenames(self, folder_name):
        print(f"📂 開始列出資料夾 {folder_name} 的檔案")  # 除錯用
        path = os.path.join(settings.BASE_DIR, 'static', 'heatmaps', folder_name, 'AN_L')
        if not os.path.isdir(path):
            print("❌ 資料夾不存在：", path)
            await self.send(json.dumps({
                "type": "heatmap_files",
                "folder": folder_name,
                "files": []
            }))
            return

        files = [f for f in os.listdir(path) if f.endswith('.svg')]
        print("✅ 找到檔案：", files)
        await self.send(json.dumps({
            "type": "heatmap_files",
            "folder": folder_name,
            "files": files
        }))


class TrainingConsumer(AsyncWebsocketConsumer):
    # 前端一連線，就會被加入到一個名叫 "training_group" 的群組，這樣 Celery 就能廣播訊息給這些人。
    async def connect(self):
        # 當前端透過 ws://.../ws/train/ 連線進來時
        # 把這個連線加入 "training_group"
        await self.channel_layer.group_add("training_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # 當前端斷線時，移除 group 成員
        await self.channel_layer.group_discard("training_group", self.channel_name)

    # Celery 呼叫的 type=training.log 會進來這裡
    async def training_log(self, event):
        message = event["message"]
        # 檢查 celery 傳來的訊息
        # logger.info("consumer.py 收到: %s", message)
        # 把 Celery 任務的 log（stdout）即時推送到前端的 WebSocket
        await self.send(text_data=message)


class TestingConsumer(AsyncWebsocketConsumer):
    # 前端一連線，就會被加入到一個名叫 "testing_group" 的群組，這樣 Celery 就能廣播訊息給這些人。
    async def connect(self):
        # 當前端透過 ws://.../ws/train/ 連線進來時
        # 把這個連線加入 "testing_group"
        await self.channel_layer.group_add("testing_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # 當前端斷線時，移除 group 成員
        await self.channel_layer.group_discard("testing_group", self.channel_name)

    # Celery 呼叫的 type=testing.log 會進來這裡
    async def testing_log(self, event):
        message = event["message"]
        # 檢查 celery 傳來的訊息
        # logger.info("consumer.py 收到: %s", message)
        # 把 Celery 任務的 log（stdout）即時推送到前端的 WebSocket
        await self.send(text_data=message)

class DeployingConsumer(AsyncWebsocketConsumer):
    # 前端一連線，就會被加入到一個名叫 "testing_group" 的群組，這樣 Celery 就能廣播訊息給這些人。
    async def connect(self):
        # 當前端透過 ws://.../ws/DEPLOY/ 連線進來時
        # 把這個連線加入 "deploying_group"
        await self.channel_layer.group_add("deploying_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # 當前端斷線時，移除 group 成員
        await self.channel_layer.group_discard("deploying_group", self.channel_name)

    # Celery 呼叫的 type=testing.log 會進來這裡
    async def deploying_log(self, event):
        message = event["message"]
        # 檢查 celery 傳來的訊息
        # logger.info("consumer.py 收到: %s", message)
        # 把 Celery 任務的 log（stdout）即時推送到前端的 WebSocket
        await self.send(text_data=message)