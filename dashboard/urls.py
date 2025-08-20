from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('withdrawal/request/', views.withdrawal_request, name='withdrawal_request'),
    path('designer/withdrawal/request/', views.designer_withdrawal_request, name='designer_withdrawal_request'),
    path('withdrawal/history/', views.withdrawal_history, name='withdrawal_history'),
    path('bonus/request/', views.bonus_request, name='bonus_request'),
    path('orders/manage/', views.manage_orders, name='manage_orders'),
    path('products/manage/', views.manage_products, name='manage_products'),
    path('designs/submit/', views.submit_design, name='submit_design'),
    path('designs/manage/', views.manage_designs, name='manage_designs'),
    path('stats/orders/', views.order_stats, name='order_stats'),
    path('withdrawal/update/<int:withdrawal_id>/', views.update_withdrawal, name='update_withdrawal'),
    path('withdrawal/delete/<int:withdrawal_id>/', views.delete_withdrawal, name='delete_withdrawal'),
    path('bonus/update/<int:bonus_id>/', views.update_bonus, name='update_bonus'),
    path('bonus/delete/<int:bonus_id>/', views.delete_bonus, name='delete_bonus'),
    path('marketer/search/', views.search_marketer, name='search_marketer'),
    path('designer/search/', views.search_designer, name='search_designer'),
    path('marketer/update/<str:username>/', views.update_marketer, name='update_marketer'),
    path('marketer/delete/<str:username>/', views.delete_marketer, name='delete_marketer'),
    path('designer/update/<str:username>/', views.update_designer, name='update_designer'),
    path('designer/delete/<str:username>/', views.delete_designer, name='delete_designer'),
    path('order-item/update/<int:order_item_id>/', views.update_order_item, name='update_order_item'),
    path('order-item/delete/<int:order_item_id>/', views.delete_order_item, name='delete_order_item'),
    path('withdrawals/manage/', views.manage_withdrawals, name='manage_withdrawals'),
    path('bonuses/manage/', views.manage_bonuses, name='manage_bonuses'),
    path('set-theme/', views.set_theme, name='set_theme'),
    path('set-language/', views.set_language, name='set_language'),
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('top_performers/', views.top_performers, name='top_performers'),

]