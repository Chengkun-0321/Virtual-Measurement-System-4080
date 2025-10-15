from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.conf import settings
from django.middleware.csrf import rotate_token
from django.middleware.csrf import get_token
import time

# 表單登入
def login_view(request):
    # print("目前 CSRF Token:", get_token(request)) 
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            rotate_token(request)
            messages.success(request, "登入成功 ✅")
            return render(request, "blog/login.html", {"redirect": True})
        else:
            messages.error(request, "帳號或密碼錯誤 ❌")

    return render(request, "blog/login.html")


# API 登入（給 JS fetch）
@csrf_exempt
def login_api(request):
    if request.method == "POST":
        account = request.POST.get("account")
        password = request.POST.get("password")

        user = authenticate(request, username=account, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"status": "success", "message": "登入成功 ✅"})
        else:
            return JsonResponse({"status": "error", "message": "帳號或密碼錯誤 ❌"})
    return JsonResponse({"status": "error", "message": "只允許 POST"})

# 登出
def logout_view(request):
    auth_logout(request)
    request.session.flush()
    rotate_token(request)
    return redirect("login")