from django.urls import path
from . import views
from blog.views import ping_test
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('ping/', ping_test, name='ping_test'),
    path('', views.home, name='home'),                             # 首頁
    path('train/', views.run_mamba_local, name='train'),           # 模型訓練頁
    path('test/', views.test_model, name='test'),                  # 測試模型頁
    path('models/', views.manage_models, name='models'),           # 模型管理頁
    path('results/', views.show_results, name='results'),          # 顯示結果頁
    path('api/list_checkpoint/', views.list_checkpoint, name='list_checkpoint'),
    path('api/delete_local_weights/', views.delete_local_weights, name='delete_local_weights'),
    path('api/rename_checkpoint/', views.rename_checkpoint, name='rename_checkpoint'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)