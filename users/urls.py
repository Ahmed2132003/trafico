# users/urls.py
from django.urls import path
from .views import (
    register_view, verify_email, login_view, logout_view,
    forget_password, reset_password
)

app_name = 'users'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('verify-email/', verify_email, name='verify_email'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forget-password/', forget_password, name='forget_password'),
    path('reset-password/', reset_password, name='reset_password'),
]