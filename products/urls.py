from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.all_list, name= 'product_list'),
    path('product/<id>/', views.product_details, name= 'product_details'),
    # path('banner_list/<id>/', views.banner_list, name= 'banner_list'), # to delete
    path('search_list/', views.search_list, name= 'search_list'),
    path('search_list/<search>/', views.search_list, name= 'search_list'),

    
    # admin side
    path('products-management/', views.product_management, name= 'product_management'),
    
    path('categories/add/', views.add_category, name= 'add_category'),
    path('categories/<int:category_id>/add/step2/', views.add_category_step2, name= 'add_category_step2'),
    path('categories/<int:category_id>/update/', views.update_category, name= 'update_category'),
    path('categories/<int:category_id>/update/step2/', views.update_category_step2, name= 'update_category_step2'),

    path('products/add/', views.add_product, name= 'add_product'),
    path('products/<int:product_id>/redirect/', views.redirect_add_product, name= 'redirect_add_product'),
    path('products/<int:product_id>/save-image/', views.image_saver, name= 'image_saver'),
    path('products/<int:product_id>/add/step2/', views.add_product_step2, name= 'add_product_step2'),
    path('products/<int:product_id>/add/step3/', views.add_product_step3, name= 'add_product_step3'),
    path('products/<int:product_id>/update/', views.update_product, name= 'update_product'),
    path('products/<int:product_id>/update/step2/', views.update_product_step2, name= 'update_product_step2'),
    path('products/<int:product_id>/update/step3/', views.update_product_step3, name= 'update_product_step3'),
    path('products/<int:product_id>/action/<str:action>/', views.product_action, name= 'product_action'),
    
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_profile/', views.admin_dashboard, name='admin_profile'),

    #test
    path('filter/', views.fliter_products, name= 'fliter_products'),
]
