from django.contrib import admin
from django.urls import path, include
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls', namespace='dashboard')), 
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
    path('set-language/<str:lang_code>/', views.set_language, name='set_language'),
]
