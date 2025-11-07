# blog/urls.py
"""
    blog 應用的 URL 配置檔。
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import path
from blog.view import *
from blog.view.views import *

# 用於在未登入/已登入時做導向
def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('home_view')     # 已登入 -> home
    return redirect('login_view')   # 未登入 -> login

urlpatterns = [
    # 根路徑：根據是否登入導向不同頁面
    # 先前曾用 lambda 快速導向，改為具名函式便於擴充與除錯
    path('', root_redirect, name='root'),

    # ---------- 認證與帳號相關 ----------
    path("login/", login_view, name="login_view"),
    path('logout/', logout, name='logout'),
    path("api/login/", login_api, name="login_api"),
    path("register/", register_view, name="register_view"),
    path("forgot_password/", forgot_password_view, name="forgot_password_view"),

    # 密碼重設流程（採用 Django 內建 view，並指定 template）
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            html_email_template_name="registration/password_reset_email.html",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    # 自訂的密碼重設確認處理（使用自訂 view 而非內建 view）
    path(
        "reset/<uidb64>/<token>/",
        custom_password_reset_confirm,
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    # ---------- 主畫面 ----------
    path("home/", home_view, name="home_view"),

    # ---------- 任務與模型相關（API 與頁面） ----------
    # 取得任務列表狀態（例如 Celery 任務）
    path("api/tasks/", tasks_status, name="tasks_status"),
    path("task/<str:task_id>/", Celery_task_status, name="task_status"),

    # 訓練相關頁面與 API
    path("train/", train_view, name="model_train_view"),
    path("api/train/", train_api, name="model_train_api"),

    # 測試相關（頁面 + 多個 API）
    path("test/", test_view, name="model_test_view"),
    path("api/test/", test_api, name="model_test_api"),
    path("api/test_list_checkpoints/", test_list_checkpoints, name="test_list_checkpoints"),
    path("api/post_test_images/", post_test_images, name="post_test_images"),
    path("api/get_test_image/<str:model_name>/<str:filename>", get_test_image, name="get_test_image"),

    # 模型管理（列出模型、刪除/重新命名檔案等）
    path("manage/", manage_models, name="model_manage_view"),
    path("api/list_checkpoint/", list_checkpoint, name="list_checkpoint"),
    path("api/delete_local_weights/", delete_local_weights, name="delete_local_weights"),
    path("api/rename_checkpoint/", rename_checkpoint, name="rename_checkpoint"),

    # 部署相關
    path("deploy/", model_deploy, name="model_deploy_view"),
    path("api/predict/", predict_api, name="model_predict_api"),
    path("api/download_sample/", download_random_100, name="download_sample"),
    path("api/deploy_list_checkpoints/", deploy_list_checkpoints, name="deploy_list_checkpoints"),
    path("api/import_npy/", import_npy, name="import_npy"),
    

    # 資料分析頁面與相關 API
    path("data_analysis/", data_analysis, name="data_analysis_view"),
    path("api/list_model_names/", list_model_names, name="list_model_names"),
    path("api/get_model_images/", get_model_images, name="get_model_images"),
    path("api/download_model/", download_model, name="download_model"),
    path("api/get_image/<str:folder>/<str:filename>", get_result_image, name="get_result_image"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
