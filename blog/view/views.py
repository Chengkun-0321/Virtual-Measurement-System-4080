from django.http import JsonResponse, HttpResponse
from celery.result import AsyncResult
from mysite.celery import app
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
import logging

logger = logging.getLogger(__name__)


# -----------------------------
# 排程處理
def tasks_status(request):
    i = app.control.inspect()

    tasks = {
        "running": [],
        "waiting": [],
        "finished": []
    }

    # 取得執行中任務 (active)
    active = i.active() or {}
    for worker, worker_tasks in active.items():
        for t in worker_tasks:
            tasks["running"].append({
                "id": t["id"],
                "name": t["name"],
                "status": "running"
            })

    # 取得等待中任務 (reserved + scheduled)
    reserved = i.reserved() or {}
    scheduled = i.scheduled() or {}
    for worker, worker_tasks in reserved.items():
        for t in worker_tasks:
            tasks["waiting"].append({
                "id": t["id"],
                "name": t["name"],
                "status": "waiting"
            })
    for worker, worker_tasks in scheduled.items():
        for t in worker_tasks:
            tasks["waiting"].append({
                "id": t["id"],
                "name": t["name"],
                "status": "waiting"
            })

    # 檢查 Redis 裡的結果 (已完成 / 失敗)
    # 這裡你需要有任務的 task_id，通常你下 .delay() 時會存起來
    # 這裡示範直接查幾個已知的 task_id
    recent_ids = request.GET.getlist("task_ids", [])  # 前端傳 task_ids 過來
    for task_id in recent_ids:
        res = AsyncResult(task_id)
        if res.state in ["SUCCESS", "FAILURE"]:
            tasks["finished"].append({
                "id": task_id,
                "name": res.task_name,
                "status": res.state.lower()
            })
    if not i:
        return JsonResponse({"running": [], "waiting": [], "finished": []})
    else:
        return JsonResponse(tasks)


# -----------------------------
# 查 Celery 任務狀態的 API
def Celery_task_status(request, task_id):
    res = AsyncResult(task_id, app=app)
    return JsonResponse({
        "task_id": task_id,
        "status": res.status,
        "result": res.result if res.ready() else None
    })


# -----------------------------
# 註冊處理
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # 記錄 POST 請求以便偵錯（請在終端查看 runserver 輸出）
        logger.info("register_view POST received: username=%s email=%s", username, email)

        # 驗證邏輯
        if password1 != password2:
            messages.error(request, "兩次輸入的密碼不一致！")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "使用者名稱已存在！")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email 已被註冊！")
            return redirect("register")

        # 建立使用者
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        # 自動登入
        login(request, user)
        messages.success(request, "註冊成功！已自動登入。")
        return redirect("home")

    # GET 請求 → 顯示註冊頁面
    return render(request, "registration/register.html")


# -----------------------------
# 密碼重設確認處理
def custom_password_reset_confirm(request, uidb64, token):
    try:
        # 嘗試從 uidb64 解出使用者 ID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    # 驗證 token 是否有效
    valid_token = user is not None and default_token_generator.check_token(user, token)

    if request.method == "POST":
        password1 = request.POST.get("new_password1")
        password2 = request.POST.get("new_password2")

        if not password1 or not password2:
            messages.error(request, "請輸入完整的密碼。")
        elif password1 != password2:
            messages.error(request, "兩次密碼不一致！")
        elif not valid_token:
            messages.error(request, "無效或已過期的重設連結。")
        else:
            user.set_password(password1)
            user.save()
            messages.success(request, "請重新登入。")
            return redirect("password_reset_complete")

    context = {"validlink": valid_token}
    return render(request, "registration/password_reset_confirm.html", context)