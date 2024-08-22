from django.urls import path
from .  import views
from django.conf.urls import handler403


urlpatterns = [
    path('', views.user_home, name='home'),
    path('wishlist', views.user_wishlist, name='wishlist'), 
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    path('wallet', views.user_wallet, name='wallet'),
    path('referral', views.user_referral, name='referral'),

    path('logout/', views.logout_page, name='logout'),
    path('login/', views.login_page, name='login'),
    path('login/forgot-password', views.forgot_password, name='forgot_password'),
    path('login/forgot-password/submit_otp', views.submit_otp, name='submit_otp'),
    path('login/forgot-password/submit_otp/resend_otp', views.resend_otp, name='resend_otp'),
    path('login/forgot-password/submit_otp/change_password', views.change_password, name='change_password'),
    path('register/', views.register_page, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),

    path('user_profile/profile_info/', views.user_profile, name='user_profile'),
    path('user_profile/address/', views.address_management, name='address_management'),
    path('user_profile/get-address-details/<int:address_id>/', views.get_address_details, name='get_address_details'),
    path('user_profile/edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('user_profile/delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('user_profile/reset_password/', views.reset_password, name='reset_password'),

    # admin
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_dashboard/', views.admin_dashboard, name='dashboard'),
    path('user_management/', views.user_management, name='user_management'),
    path('user_management/user_action/<action>/<id>/', views.user_action, name= 'user_action'),
    path('permission-denied/', views.permission_denied_view, name='permission_denied'),
]


