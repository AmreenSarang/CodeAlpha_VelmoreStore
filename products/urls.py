
from django.urls import path
from . import views

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),

    # Products
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    # Shopping cart
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove-from-cart/<int:id>/', views.remove_from_cart, name='remove_from_cart'),
    path('increase/<int:id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:id>/', views.decrease_quantity, name='decrease_quantity'),

    # User accounts
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Checkout and orders
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.my_orders, name='orders'),

    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
