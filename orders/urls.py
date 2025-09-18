from django.urls import path
from . import views


urlpatterns = [
    path('cart/', views.cart_view, name= 'cart'),
    path('cart/add/', views.add_to_cart, name= 'add_to_cart'),
    path('cart/update/', views.update_cart, name= 'update_cart'),
    path('cart/delete-item/', views.delete_cart_item, name= 'delete_cart_item'),

    path('checkout/', views.checkout_page, name= 'checkout_page'),
    path('checkout/delivery-charge/', views.get_delivery_charge_for_checkout, name='get_delivery_charge'),
    path('checkout/pay/razorpay/', views.razorpaycheck, name= 'razorpaycheck'),
    path('checkout/status/<int:order_id>/', views.order_success, name= 'order_success'),
    path('checkout/retry-stock-check/', views.retry_payment_stock_check, name= 'retry_payment_stock_check'),    
    path('checkout/retry-payment/<int:order_id>/', views.retry_payment, name= 'retry_payment'),

    path('orders/', views.user_orders_page, name= 'user_orders_page'),
    path('orders/<int:order_id>/', views.user_order_details, name= 'user_order_details'),
    path('orders/<int:order_item_id>/cancel/', views.user_order_cancel, name= 'user_order_cancel'),

    # Admin Side
    path('admin-dashboard/orders/', views.order_management, name= 'order_management'),
    path('admin-dashboard/orders/<int:order_id>/items/', views.order_item_management, name= 'order_item_management'),
    path('admin-dashboard/orders/items/<int:order_item_id>/update/', views.update_order_status, name= 'update_order_status'),
    path('admin-dashboard/return-requests/', views.return_items_management, name= 'return_items_management'),

    path('admin-dashboard/coupons/', views.admin_coupon_management, name= 'coupon_management'),
    path('admin-dashboard/coupons/add/', views.add_coupon, name= 'add_new_coupon'),
    path('admin-dashboard/coupons/<int:coupon_id>/update/', views.update_coupon, name= 'update_coupon'),
    
    path('admin-dashboard/sales-report/', views.sales_report, name= 'sales_report'),

    # test
    path('test', views.test_purpose, name= 'test'),
    path('payment_success/', views.payment_success, name='payment_success'),
]

