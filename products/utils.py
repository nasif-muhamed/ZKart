from django.core.paginator import Paginator
from .models import Category
from users.models import Wishlist
import logging

logger = logging.getLogger('products')

def product_list(request, object):
    page = int(request.GET.get('page',1))
    
    products_all = object.filter(is_active=True, category__is_active = True, stage = 'stage3').prefetch_related('product_images')

    product_paginator = Paginator(products_all, 9)
    products = product_paginator.get_page(page)
    
    start, end = 0, 0
    costum_range = range(1, products.paginator.num_pages+1)
    if products.paginator.num_pages > 3: 
        if page == 1 or page == 2:
            costum_range = range(1, 4)
            end = products.paginator.num_pages
        elif page == products.paginator.num_pages or page == products.paginator.num_pages-1:
            costum_range = range(products.paginator.num_pages-2, products.paginator.num_pages+1)
            start = 1
        else:
            costum_range = range(page-1, page+2)
            start = 1
            end = products.paginator.num_pages


    category_ids = products_all.values_list('category', flat=True)  # Includes duplicates
    categories= Category.objects.filter(is_active = True, id__in=set(category_ids))
    brands = products_all.values_list('brand', flat= True)

    logger.debug('Products paginated result: %s', products)
    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(account = request.user.account).values_list('product', flat=True)

    url_string = "?form_submitted={{ request.GET.form_submitted }}&search={{ request.GET.search }}&sort={{ request.GET.sort }}\
    &gender={{ request.GET.gender }}{% for i in request|getlist:'category' %}&category={{i}}{%endfor%}{% for i in request|getlist:'brand' %}\
    &brand={{i}}{%endfor%}&price_min={{ request.GET.price_min }}&price_max={{ request.GET.price_max }}"
    context = {
        'categories': categories,
        'brands' : set(brands),
        'products': products,
        'range': costum_range,
        'start': start,
        'end': end,
        'user_wishlist' : user_wishlist,
        'url_string': url_string,
    }

    # return render(request, 'product_list.html', context)
    return context

