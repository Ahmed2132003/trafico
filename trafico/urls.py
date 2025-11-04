from django.contrib import admin
from django.urls import path, include
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls', namespace='products')), 
    path('users/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('set-language/<str:lang_code>/', views.set_language, name='set_language'),
]
