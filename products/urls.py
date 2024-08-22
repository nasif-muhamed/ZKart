from django.urls import path
from . import views

urlpatterns = [
    path('product_details/<id>', views.product_details, name= 'product_details'),
    path('product_list', views.all_list, name= 'product_list'),
    path('banner_list/<id>', views.banner_list, name= 'banner_list'),
    path('search_list/', views.search_list, name= 'search_list'),
    path('search_list/<search>/', views.search_list, name= 'search_list'),

    
    # admin side
    path('product_management/', views.product_management, name= 'product_management'),
    path('product_management/add_category/', views.add_category, name= 'add_category'),
    path('product_management/add_category2/<int:category_id>', views.add_category2, name= 'add_category2'),

    path('product_management/update_category/<int:category_id>', views.update_category, name= 'update_category'),
    path('product_management/update_category2/<int:category_id>', views.update_category2, name= 'update_category2'),

    path('product_management/add_product/', views.add_product, name= 'add_product'),
    path('product_management/redirect-add-product/<int:product_id>/', views.redirect_add_product, name= 'redirect_add_product'),
    path('product_management/image_saver/<int:product_id>/', views.image_saver, name= 'image_saver'),
    path('product_management/add_product2/<int:product_id>/', views.add_product2, name= 'add_product2'),
    path('product_management/add_product3/<int:product_id>/', views.add_product3, name= 'add_product3'),

    path('product_management/update_product/<id>/', views.update_product, name= 'update_product'),
    path('product_management/update_product2/<id>/', views.update_product2, name= 'update_product2'),
    path('product_management/update_product3/<id>/', views.update_product3, name= 'update_product3'),

    path('product_management/product_action/<action>/<id>/', views.product_action, name= 'product_action'),
    
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_profile/', views.admin_dashboard, name='admin_profile'),

    #test
    path('filter', views.fliter_products, name= 'fliter_products'),
]
