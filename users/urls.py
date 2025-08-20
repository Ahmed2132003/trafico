from django.urls import path
from .views import register_view, verify_email, login_view, logout_view
app_name = 'users'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('verify-email/', verify_email, name='verify_email'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]