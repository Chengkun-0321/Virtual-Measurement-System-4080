import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.middleware.csrf import rotate_token
from django.middleware.csrf import get_token

# 表單登入
def login_view(request):
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

            csrf_token = get_token(request)  # 取得新的 CSRF token

            return HttpResponse(
                        json.dumps({
                            "status": "success",
                            "message": "登入成功 ✅",
                            "csrfToken": csrf_token
                        }, indent=4, ensure_ascii=False),
                        content_type="application/json"
                    )
        else:
            return HttpResponse(
                        json.dumps({"status": "error", "message": "帳號或密碼錯誤 ❌"}, indent=4, ensure_ascii=False),
                        content_type="application/json"
                    )
    return JsonResponse({"status": "error", "message": "只允許 POST"})

# 登出
def logout(request):
    auth_logout(request)
    request.session.flush()
    rotate_token(request)
    return redirect("login_view")