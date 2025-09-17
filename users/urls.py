from django.urls import path, include
from .  import views


urlpatterns = [
    path('', views.user_home, name='home'),
    path('wishlist', views.user_wishlist, name='wishlist'), 
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    # path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    path('wallet', views.user_wallet, name='wallet'),
    path('referral', views.user_referral, name='referral'),

    path('logout/', views.logout_page, name='logout'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path("forgot-password/", include([
        path('', views.forgot_password, name='forgot_password'),
        path('submit-otp/', views.submit_otp, name='submit_otp'),
        path('resend-otp/', views.resend_otp, name='resend_otp'),
        path('change-password/', views.change_password, name='change_password'),
    ])),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),

    path("profile/", views.user_profile, name="user_profile"),
    path("addresses/", views.address_management, name="address_management"),
    path("addresses/<int:address_id>/", views.get_address_details, name="get_address_details"),
    path("addresses/<int:address_id>/edit/", views.edit_address, name="edit_address"),
    path("addresses/<int:address_id>/delete/", views.delete_address, name="delete_address"),
    path("reset-password/", views.reset_password, name="reset_password"),

    # admin
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='dashboard'),
    path('user-management/', views.user_management, name='user_management'),
    path('user-management/<int:user_id>/action/<str:action>/', views.user_action, name= 'user_action'),
    path('permission-denied/', views.permission_denied_view, name='permission_denied'),
]
