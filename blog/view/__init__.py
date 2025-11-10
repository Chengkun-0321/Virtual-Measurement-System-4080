from .login import login_view, login_api, logout
from .register import register_view
from .forgot_password import forgot_password_view
from .home import home_view
from .model_train import train_view, train_api
from .model_test import test_view, test_api, test_list_checkpoints, post_test_images
from .model_deploy import model_deploy, download_random_100, import_data, predict_api, deploy_list_checkpoints
from .model_manage import manage_models, list_checkpoint, delete_checkpoint, rename_checkpoint
from .data_analysis import data_analysis, list_model_names, download_model, get_result_image, get_model_images
from .views import tasks_status, Celery_task_status