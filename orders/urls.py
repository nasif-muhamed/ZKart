from django.urls import path
from . import views


urlpatterns = [
    path('cart/', views.cart_view, name= 'cart'),
    path('add-to-cart/', views.add_to_cart, name= 'add_to_cart'),
    path('update-cart/', views.update_cart, name= 'update_cart'),
    path('delete-cart-item/', views.delete_cart_item, name= 'delete_cart_item'),
    path('checkout/', views.checkout_page, name= 'checkout_page'),
    path('get-delivery-charge/', views.get_delivery_charge_for_checkout, name='get_delivery_charge'),
    path('proceed-to-pay-razorpay/', views.razorpaycheck, name= 'razorpaycheck'),
    path('order-success/<order_id>/', views.order_success, name= 'order_success'),
    path('retry-stock-check/', views.retry_payment_stock_check, name= 'retry_payment_stock_check'),    
    path('retry-payment/<order_id>/', views.retry_payment, name= 'retry_payment'),

    path('my-orders/', views.user_orders_page, name= 'user_orders_page'),
    path('my-order-details/<order_id>/', views.user_order_details, name= 'user_order_details'),
    path('my-order-cancel/<order_item_id>/', views.user_order_cancel, name= 'user_order_cancel'),

    # Admin Side
    path('order-management/', views.order_management, name= 'order_management'),
    path('order-item-management/<order_id>/', views.order_item_management, name= 'order_item_management'),
    path('order-item-update/<order_item_id>/', views.update_order_status, name= 'update_order_status'),
    path('return-request-orders/', views.return_items_management, name= 'return_items_management'),

    path('coupon-management/', views.admin_coupon_management, name= 'coupon_management'),
    path('add-coupon/', views.add_coupon, name= 'add_new_coupon'),
    path('update-coupon/<coupon_id>/', views.update_coupon, name= 'update_coupon'),
    
    path('sales-report/', views.sales_report, name= 'sales_report'),
    # test
    path('test', views.test_purpose, name= 'test'),
    path('payment_success/', views.payment_success, name='payment_success'),
]

