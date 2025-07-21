from django.urls import path
from . import views
from blog.views import ping_test
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('ping/', ping_test, name='ping_test'),
    path('', views.home, name='home'),                                   # 首頁
    path('train/', views.run_mamba_local, name='train'),                 # 模型訓練頁面
    path('test/', views.test_model, name='test'),                        # 測試模型頁面
    path('api/get_image/<str:folder>/<str:filename>/', views.get_result_image),
    path('models/', views.manage_models, name='models'),                 # 模型管理頁面
    path('api/list_checkpoint/', views.list_checkpoint, name='list_checkpoint'),
    path('api/delete_local_weights/', views.delete_local_weights, name='delete_local_weights'),
    path('api/rename_checkpoint/', views.rename_checkpoint, name='rename_checkpoint'),
    path("deploy_model/", views.deploy_model, name="deploy_model"),       # 部署模型
    path("run_model/", views.run_model, name="run_model"),                # 啟動模型
    path('download/', views.data_download, name='data'),                  # 資料下載頁面
    path('download/file/<str:file_type>/<str:model_name>/', views.download_file, name='download_file'),
    path('api/list_model_names/', views.list_model_names, name='list_model_names'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)