from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('constructor/', views.constructor_view, name='constructor'),
    path('cart/', views.cart_view, name='cart'),
    path('buy/<int:bouquet_id>/', views.buy_ready_bouquet, name='buy_ready'),
    path('checkout/<int:bouquet_id>/', views.checkout_view, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    
    path('florist/', views.florist_dashboard, name='florist_dashboard'),
    path('florist/upload/<int:order_id>/', views.upload_photo, name='upload_photo'),
    
    path('courier/', views.courier_dashboard, name='courier_dashboard'),
    path('courier/deliver/<int:order_id>/', views.mark_delivered, name='mark_delivered'),
    
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('api/search/', views.search_api, name='search_api'),
    
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('approve-photo/<int:photo_id>/', views.approve_photo, name='approve_photo'),
    path('export-csv/', views.export_orders_csv, name='export_csv'),

    path('cart/increase/<int:item_id>/', views.increase_item, name='increase_item'),
    path('cart/decrease/<int:item_id>/', views.decrease_item, name='decrease_item'),
    path('cart/remove/<int:item_id>/', views.remove_item, name='remove_item'),

    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html', success_url='/profile/'), name='password_change'),
]