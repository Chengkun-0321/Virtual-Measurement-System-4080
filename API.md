# 專案 API 說明

本文檔列出後端主要 JSON / 檔案下載 / WebSocket 端點。頁面型 (HTML) 只簡述。  
回應中出現的 `status` 通常為：`success | submitted | error`。  
部分 API 使用 `@csrf_exempt`，若未豁免請送出 `X-CSRFToken`。

---

## 目錄
1. 認證 / 使用者
2. 任務 / 排程
3. 模型訓練
4. 模型測試
5. 模型部署 (預測)
6. 模型管理 (檔案操作)
7. 資料分析 (曲線 / 圖片 / 模型下載)
8. 圖片 / 檔案存取
9. WebSocket 通道
10. 回傳格式摘要

---

## 1. 認證 / 使用者

| 類型 | Method | Path | 說明 |
|------|--------|------|------|
| Page | GET | `/login/` | 登入頁面 ([`login_view`](blog/view/login.py)) |
| API  | POST | `/api/login/` | 表單 / Fetch 方式登入 ([`login_api`](blog/view/login.py)) |
| Page | POST | `/logout/` | 表單登出 ([`logout`](blog/view/login.py)) |
| Page | GET | `/register/` | 註冊頁 (視圖匯入於 [`__init__`](blog/view/__init__.py)) |

### /api/login/ 範例
Request (multipart form)
```
account=testuser&password=secret
```
Response
```json
{
  "status": "success",
  "message": "登入成功 ✅",
  "csrfToken": "新 CSRF Token"
}
```

---

## 2. 任務 / 排程

| Method | Path | 說明 |
|--------|------|------|
| GET | `/api/tasks/` | 目前執行 / 等待 / 已完成列表 ([`tasks_status`](blog/view/views.py)) |
| GET | `/task/<task_id>/` | 查單一 Celery 任務狀態 ([`Celery_task_status`](blog/view/views.py)) |

Response 範例 (`/api/tasks/`)
```json
{
  "running": [{ "id": "...", "name": "blog.tasks.train_model", "status": "running" }],
  "waiting": [],
  "finished": []
}
```

---

## 3. 模型訓練

| 類型 | Method | Path | 說明 |
|------|--------|------|------|
| Page | GET | `/train/` | 訓練頁面 ([`train_view`](blog/view/model_train.py)) |
| API  | POST | `/api/train/` | 提交訓練任務 → Celery ([`train_api`](blog/view/model_train.py)) |

POST Body
```json
{
  "model": "Mamba",
  "dataset": "PETBottle",
  "epochs": "50",
  "batch_size": "16",
  "learning_rate": "0.001",
  "validation_freq": "1"
}
```
成功回應
```json
{
  "status": "submitted",
  "task_id": "celery-task-id",
  "message": "已提交訓練: 模型=Mamba, 資料集=PETBottle"
}
```

背景任務函式：[`train_model`](blog/tasks.py)

---

## 4. 模型測試

| 類型 | Method | Path | 說明 |
|------|--------|------|------|
| Page | GET | `/test/` | 測試頁 ([`test_view`](blog/view/model_test.py)) |
| API  | POST | `/api/test/` | 提交測試任務 ([`test_api`](blog/view/model_test.py)) |
| API  | POST | `/api/test_list_checkpoints/` | 列出可用 `.h5` ([`test_list_checkpoints`](blog/view/model_test.py)) |
| API  | POST | `/api/post_test_images/` | 測試完成回傳圖片 URL 映射 ([`post_test_images`](blog/view/model_test.py)) |
| File | GET | `/api/get_test_image/<model>/<filename>` | 測試輸出圖片 ([`get_test_image`](blog/view/model_test.py)) |

提交測試 Body
```json
{
  "model": "Mamba",
  "dataset": "PETBottle",
  "checkpoint_path": "checkpoint名稱(不含.h5?)",
  "mean": "65.0",
  "boundary_upper": "70.0",
  "boundary_lower": "60.0"
}
```

成功回應
```json
{
  "status": "submitted",
  "task_id": "celery-task-id",
  "message": "已提交測試: 模型=Mamba, 資料集=PETBottle, checkpoint=..."
}
```

背景任務：[`test_model`](blog/tasks.py)

---

## 5. 模型部署 (預測)

| 類型 | Method | Path | 說明 |
|------|--------|------|------|
| Page | GET | `/deploy/` | 部署頁面 ([`model_deploy`](blog/view/model_deploy.py)) |
| API  | GET | `/api/deploy_list_checkpoints/` | 可用模型列表 ([`deploy_list_checkpoints`](blog/view/model_deploy.py)) |
| File | GET | `/api/download_sample/` | 下載隨機 100 筆 `sampled_100.npy` ([`download_random_100`](blog/view/model_deploy.py)) |
| API  | POST | `/api/import_data/` | 上傳 `.npy` (預覽儲存) ([`import_data`](blog/view/model_deploy.py)) |
| API  | POST | `/api/predict/` | 提交預測任務→Celery ([`predict_api`](blog/view/model_deploy.py)) |

預測提交 Body
```json
{
  "indices": [0, 2, 5],
  "model": "模型名稱(不含.h5)"
}
```
成功回應
```json
{
  "status": "submitted",
  "task_id": "celery-task-id",
  "message": "預測任務已提交"
}
```

背景任務：[`predict_model`](blog/tasks.py)

---

## 6. 模型管理

| 類型 | Method | Path | 說明 |
|------|--------|------|------|
| Page | GET | `/manage/` | 管理頁 ([`manage_models`](blog/view/model_manage.py)) |
| API  | GET | `/api/list_checkpoint/` | 列出本機模型/大小/時間/acc ([`list_checkpoint`](blog/view/model_manage.py)) |
| API  | POST | `/api/delete_checkpoint/` | 刪除多個模型 ([`delete_checkpoint`](blog/view/model_manage.py)) |
| API  | POST | `/api/rename_checkpoint/` | 重新命名模型/對應資料夾/JSON ([`rename_checkpoint`](blog/view/model_manage.py)) |

刪除 Body
```json
{ "filenames": ["modelA", "modelB"] }
```
改名 Body
```json
{ "old_name": "oldModel", "new_name": "newModel" }
```

---

## 7. 資料分析

| 類型 | Method | Path | 說明 |
|------|--------|------|------|
| Page | GET | `/data_analysis/` | 分析頁 ([`data_analysis`](blog/view/data_analysis.py)) |
| API  | POST | `/api/list_model_names/` | 模型名稱列表 ([`list_model_names`](blog/view/data_analysis.py)) |
| API  | POST | `/api/get_model_images/` | 回傳各曲線圖 URL 映射 ([`get_model_images`](blog/view/data_analysis.py)) |
| API  | POST | `/api/download_model/` | 下載 `.h5` ([`download_model`](blog/view/data_analysis.py)) |
| File | GET | `/api/get_image/<folder>/<filename>` | 單張訓練圖 (通用) ([`get_result_image`](blog/view/data_analysis.py)) |

`/api/get_model_images/` 回應
```json
{
  "images": {
    "mape": "/api/get_image/<model>/training_mape_curve.png",
    "mse": "...",
    "loss": "...",
    "mae": "...",
    "gt": "/api/get_image/<model>/ground_truth.png"
  }
}
```

---

## 8. 圖片 / 檔案存取

| Path | 用途 |
|------|------|
| `/api/get_test_image/<model>/<filename>` | 測試完成的混淆矩陣等 |
| `/api/get_image/<folder>/<filename>` | 訓練曲線、ground truth 圖 |

---

## 9. WebSocket 通道

定義於 [`websocket_urlpatterns`](blog/routing.py) 與 ASGI 配置 [`mysite/asgi.py`](mysite/asgi.py)。  
Consumer 實作於 [`consumers.py`](blog/consumers.py)。

| 路徑 | 群組 | 主要用途 | 典型訊息 |
|------|------|----------|----------|
| `/ws/TRAIN/` | `training_group` | 訓練即時 log | `{"type":"training.log","message":"..."}` |
| `/ws/TEST/`  | `testing_group`  | 測試即時 log | `{"type":"testing.log","message":"..."}` |
| `/ws/DEPLOY/`| `deploying_group`| 部署 / 預測 log / RESULT | `RESULT:[...]` |
| `/ws/CMD/`   | 無固定群組 (多功能) | 測試指令 / 列表請求 / 熱圖檔案 | 自定字串或 JSON |

典型完成訊號：`__FINISHED__`。  
預測結果：行中以 `RESULT:` 開頭的 JSON-like 陣列。

---

## 10. 回傳格式摘要

| 場景 | 成功 | 失敗 |
|------|------|------|
| 提交任務 | `{ "status":"submitted", "task_id": "...", "message": "..." }` | `{ "status":"error", "message": "..."} 或 HTTP 4xx/5xx` |
| 一般列表 | 自訂欄位 (e.g. `{"checkpoints":[...]}`) | 空陣列或 `{"error":"..."}` |
| 檔案下載 | 二進位串流 (FileResponse) | 404 / `{"error":"..."}` |

---

## 11. 速查 cURL 範例

訓練提交
```bash
curl -X POST http://HOST/api/train/ \
  -H "Content-Type: application/json" \
  -d '{"model":"Mamba","dataset":"PETBottle","epochs":"10","batch_size":"16","learning_rate":"0.001","validation_freq":"1"}'
```

測試提交
```bash
curl -X POST http://HOST/api/test/ \
  -H "Content-Type: application/json" \
  -d '{"model":"Mamba","dataset":"PETBottle","checkpoint_path":"ckpt_01","mean":"65.0","boundary_upper":"70.0","boundary_lower":"60.0"}'
```

預測提交
```bash
curl -X POST http://HOST/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"indices":[0,1,2],"model":"MyModel"}'
```

下載模型
```bash
curl -X POST http://HOST/api/download_model/ \
  -H "Content-Type: application/json" \
  -d '{"model_name":"MyModel"}' -o MyModel.h5
```

---

## 12. 主要相關檔案索引

- URL 定義: [`blog/urls.py`](blog/urls.py)
- 訓練任務: [`train_model`](blog/tasks.py)
- 測試任務: [`test_model`](blog/tasks.py)
- 預測任務: [`predict_model`](blog/tasks.py)
- 訓練視圖: [`train_api`](blog/view/model_train.py)
- 測試視圖: [`test_api`](blog/view/model_test.py)
- 部署視圖: [`predict_api`](blog/view/model_deploy.py)
- 模型管理: [`list_checkpoint`](blog/view/model_manage.py), [`delete_checkpoint`](blog/view/model_manage.py), [`rename_checkpoint`](blog/view/model_manage.py)
- 分析視圖: [`get_model_images`](blog/view/data_analysis.py), [`download_model`](blog/view/data_analysis.py)
- WebSocket: [`CMDConsumer`](blog/consumers.py)
- Celery 設定: [`mysite/celery.py`](mysite/celery.py)
