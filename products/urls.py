from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_add, name='product_add'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('favorite/<int:product_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order/create/', views.create_order, name='create_order'),
    path('set-language/<str:lang_code>/', views.set_language, name='set_language'),
]