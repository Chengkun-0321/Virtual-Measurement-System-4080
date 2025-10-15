# blog/view/register.py

from django.shortcuts import render

def register_view(request):
    return render(request, "registration/register.html")