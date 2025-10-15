# blog/view/forgot_password.py

from django.shortcuts import render

def forgot_password_view(request):
    return render(request, "blog/forgot_password.html")