from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from blog.view import *
from blog.view.views import *
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('home')   # 已登入去 home
    return redirect('login')      # 沒登入去 login

urlpatterns = [
    # 根路徑直接導向 login
    # path('', lambda request: redirect('login'), name='root'),
    path('', root_redirect, name='root'),

    path("login/", login_view, name="login"),
    path('logout/', logout_view, name='logout'),
    path("login_api/", login_api, name="login_api"),
    path("register/", register_view, name="register"),
    path("forgot_password/", forgot_password_view, name="forgot_password"),

    # 密碼重設流程
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

    
    path("home/", home_view, name="home"),
    # 模型相關
    path("api/tasks/", tasks_status, name="tasks_status"),
    path("task/<str:task_id>/", Celery_task_status, name="task_status"),

    path("train/", train_view, name="train"),
    path("api/train/", train_api, name="train_api"),

    path("test/", test_view, name="test"),
    path("api/test_list_checkpoints/", test_list_checkpoints, name="test_list_checkpoints"),
    path("api/test_api/", test_api, name="test_api"),
    path("api/post_test_images/", post_test_images, name="post_test_images"),
    path("api/get_test_image/<str:model_name>/<str:filename>", get_test_image, name="get_test_image"),

    path("models/", manage_models, name="models"),
    path("api/list_checkpoint/", list_checkpoint, name="list_checkpoint"),
    path("api/delete_local_weights/", delete_local_weights, name="delete_local_weights"),
    path("api/rename_checkpoint/", rename_checkpoint, name="rename_checkpoint"),

    path("model_deploy/", model_deploy, name="model_deploy"),
    path("download_sample/", download_random_100, name="download_sample"),
    path("api/deploy_list_checkpoints/", deploy_list_checkpoints, name="deploy_list_checkpoints"),
    path("api/import_npy/", import_npy, name="import_npy"),
    path("api/predict/", predict_api, name="predict_model"),

    path("data_analysis/", data_analysis, name="data_analysis"),
    path("api/list_model_names/", list_model_names, name="list_model_names"),
    path("api/get_model_images/", get_model_images, name="get_model_images"),
    path("api/download_model/", download_model, name="download_model"),
    path("api/get_image/<str:folder>/<str:filename>", get_result_image, name="get_result_image"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
