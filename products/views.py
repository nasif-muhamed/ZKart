from django.shortcuts import render, HttpResponse, redirect
from . models import *
from users . models import *
from users . views import *
from django.db.models import Sum, F, Func, Value
from django.db.models.functions import Coalesce, Lower, Replace
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse


# Products and Category related

def product_details(request, id):
    try:
        products = Product.objects.filter(is_active=True, category__is_active = True, stage = 'stage3').prefetch_related('product_images')
        product = products.get(id=id)
        variants = product.variants.all()
        colors = variants.values('color__name', 'color__hex_code').distinct()
        sizes = variants.values_list('size__name', flat=True).distinct()
        related= products.filter(category=product.category).exclude(id=product.id)[:6]
        categories= Category.objects.values_list('name', flat=True)
        brands = Product.objects.values_list('brand', flat=True)
        user_wishlist = []
        if request.user.is_authenticated:
            user_wishlist = Wishlist.objects.filter(account = request.user.account).values_list('product', flat=True)

        context = {
            'product': product,
            'colors': list(colors),
            'sizes': list(sizes),
            'variants': variants,
            'related' : related,
            'categories' : categories,
            'brands' : set(brands),
            'user_wishlist' : user_wishlist,
        }
        return render(request, 'product_details.html', context)
    except:
        # messages.error(request, 'Product does not exist')
        return redirect(user_home)


def product_list(request, object):
    page = int(request.GET.get('page',1))
    
    products_all = object.filter(is_active=True, category__is_active = True, stage = 'stage3').prefetch_related('product_images')

    product_paginator = Paginator(products_all, 3)
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


def banner_list(request, id):
    banner_obj = Banner.objects.get(id=id)
    product_obj = banner_obj.products.all().filter(is_active=True, category__is_active = True).prefetch_related('product_images')
    show = product_list (request, product_obj)
    return render(request, 'product_list.html', show)


def all_list(request):
    products_all = Product.objects.all().filter(is_active=True, category__is_active = True).prefetch_related('product_images')

    show = product_list (request, products_all)
    return render(request, 'product_list.html', show)


def fliter_products(request):
    show = search_list(request)

    return show


def search_list(request, search=''):
    if not search and request.method == 'GET':
        search = request.GET.get('search')
        sort = request.GET.get('sort')
        filtering = request.GET.get('filter')

        if search:
            product_obj = Product.objects.filter(
                Q(title__icontains=search) |
                Q(category__name__icontains=search) |
                Q(brand__icontains=search)
            ).filter(is_active=True, category__is_active = True).prefetch_related('product_images')

        else:
            product_obj = Product.objects.filter(is_active=True, category__is_active = True).prefetch_related('product_images')

        category_ids_list = product_obj.values_list('category', flat=True)  # Includes duplicates
        categories= Category.objects.filter(is_active = True, id__in=set(category_ids_list))
        brands = product_obj.values_list('brand', flat= True)

        main_context = {
            'categories' : categories,
            'brands' : set(brands),
        }

        if 'form_submitted' in request.GET:
            gender = request.GET.get('gender')
            category_ids = request.GET.getlist('category')
            brands_filter = request.GET.getlist('brand')
            price_min = request.GET.get('price_min')
            price_max = request.GET.get('price_max')

            if gender:
                product_obj = product_obj.filter(gender = gender)

            if category_ids:
                try:
                    category_ids = list(map(int, category_ids))
                except ValueError:
                    category_ids = []
                
                product_obj = product_obj.filter(category_id__in = category_ids)

            if brands_filter:
                product_obj = product_obj.filter(brand__in = brands_filter)

            try:
                if price_min is not None and price_min:
                    product_obj = product_obj.filter(selling_price__gte = int(price_min))

                if price_max is not None and price_max:
                    product_obj = product_obj.filter(selling_price__lte = int(price_max))
            except:
                price_min = None
                price_max = None

        if sort:
            if sort == 'a2z':
                sorted_products = product_obj.order_by('title')
                
            elif sort == 'z2a':
                sorted_products = product_obj.order_by('-title')
                
            elif sort == 'l2h':
                sorted_products = product_obj.order_by('selling_price')
                
            elif sort == 'h2l':
                sorted_products = product_obj.order_by('-selling_price')
                
            elif sort == 'popular':
                sorted_products = product_obj.annotate(total_stock_ordered=Coalesce(Sum('variants__ordered_product__quantity'), 0)) \
                .order_by('-total_stock_ordered')
                
            elif sort == 'latest':
                sorted_products = product_obj.order_by('-updated_at')
                
            show = product_list (request, sorted_products)
        
        else:
            show = product_list (request, product_obj)

        context = {**show, **main_context}
        return render(request, 'product_list.html', context)
    
    if search:
        if search == 'all':
            product_obj = Product.objects.filter(is_active=True, category__is_active = True).prefetch_related('product_images')

        if search == 'men':
            product_obj = Product.objects.filter(gender='M', is_active=True, category__is_active = True).prefetch_related('product_images')
            
        if search == 'women':
            product_obj = Product.objects.filter(gender='F', is_active=True, category__is_active = True).prefetch_related('product_images')

        if search == 'unisex':
            product_obj = Product.objects.filter(gender='U', is_active=True, category__is_active = True).prefetch_related('product_images')

        if search == 'trending':
            product_obj = Product.objects.filter(trending=True, is_active=True, category__is_active = True).prefetch_related('product_images')

        if search == 'latest':
            product_obj = Product.objects.filter(is_active=True, category__is_active = True).prefetch_related('product_images')

        category = Category.objects.filter(is_active = True).values_list('name',flat=True)
        if search in category:
            product_obj = Product.objects.filter(category__name= search)

        brand = Product.objects.filter(is_active = True).values_list('brand',flat=True)
        brand = set(brand)
        if search in brand:
            product_obj = Product.objects.filter(brand= search)

        categories= Category.objects.filter(is_active = True, name__in=set(category))
        main_context = {
            'categories' : categories,
            'brands' : set(brand),
        }

        show = product_list (request, product_obj)
        context = {**show, **main_context}

        return render(request, 'product_list.html', context)
            
    return redirect(user_home)


# admin

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def product_management(request):
    products = request.user.product_creator.all()
    categories = Category.objects.all().order_by(F('is_active').desc(), '-created_at')

    product_search = request.GET.get('product_search')
    category_search = request.GET.get('category_search')       

    if product_search and product_search is not None:
        products = products.filter(title__icontains = product_search)

    if category_search and category_search is not None:
        categories = categories.filter(name__icontains = category_search)

    active_products = products.filter(is_active = True, stage = 'stage3')
    delete_products = products.filter(is_active = False, stage = 'stage3')
    incomplete_produts = products.exclude(stage = 'stage3')
    context = {
        'active_products' : active_products,
        'delete_products': delete_products,
        'categories': categories,
        'product_search' : product_search,
        'category_search' : category_search,
        'incomplete_produts' : incomplete_produts,
    }
    return render(request, 'admin_page/product_management.html', context)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def add_category(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        active = 'active' in request.POST
        module_offer = request.POST.get('offer')

        categories = Category.objects.annotate(lower_name = Lower(Replace('name', Value(' '), Value('')))).values_list('lower_name', flat=True)
        category_check = (title.lower()).replace(" ", "")
        
        if category_check in categories:
            messages.error(request, 'Category with similar title exists')
            return redirect(add_category)

        try:
            if not module_offer:
                module_offer = None
            title = title.title()
            category = Category(name=title, module_offer=module_offer, is_active=active)
            category.save()
            messages.success(request, 'Part 1 completed') 

        except IntegrityError:
            messages.error(request, 'Category with same title exists')
            return redirect(add_category)

        except:
            messages.error(request, 'Oops something went wrong')
            return redirect(add_category)
        
        return redirect(add_category2, category.id)
    
    context = {

    }
    return render(request, 'admin_page/add_category.html', context)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def add_category2(request, category_id):
    category = Category.objects.get(id=category_id)
    if request.method == 'POST':
        size_name  = request.POST.get('size')
        sizes = category.sizes.all()
        sizes_names_id = sizes.values('id', 'name')
        sizes_names = sizes.annotate(lower_name=Lower(Replace('name', Value(' '), Value('')))).values_list('lower_name', flat=True)
        size_name = (size_name.lower()).replace(" ", "")
        if size_name in sizes_names:
            return JsonResponse({'error': 'Similar Size is already added','sizes': list(sizes_names_id)}, status=400)

        if len(size_name) > 2:
            return JsonResponse({'error': 'Size can only contain 2 Characters','sizes': list(sizes_names_id)}, status=400)

        if size_name:
            size_name = size_name.upper()
            size = Size(name= size_name , category= category)
            size.save()
            return JsonResponse({'sizes': list(sizes_names_id)})
        else:
            return JsonResponse({'error': 'Input is empty','sizes': list(sizes_names_id)}, status=400)

    sizes = category.sizes.all().values('id', 'name')
    category_name = category.name
    context = {
        'category': category,
        'sizes' : sizes
    }
    return render(request, 'admin_page/add_category2.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def update_category(request, category_id):
    category = Category.objects.get(id=category_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        active = 'active' in request.POST
        module_offer = request.POST.get('offer')

        categories = Category.objects.exclude(id=category_id).annotate(lower_name = Lower(Replace('name', Value(' '), Value('')))).values_list('lower_name', flat=True)    
        category_check = (title.lower()).replace(" ", "")
        
        if category_check in categories:
            messages.error(request, 'Category with similar title exists')
            return redirect(update_category, category_id)

        try:
            changes_detected = False
            if category.name != title and title != None:
                category.name = title = title.title()
                changes_detected = True

            if category.is_active != active and active != None:
                category.is_active = active
                changes_detected = True
            
            if module_offer and category.module_offer != module_offer and module_offer != None:
                category.module_offer = module_offer
                changes_detected = True

            if changes_detected:
                category.save()
                messages.success(request, 'updated successfully')

            else:
                messages.info(request, 'No Updations')

        except:
            messages.error(request, 'Oops something went wrong')
            return redirect(update_category)


        return redirect(update_category2, category_id)

    context = {
        'category' : category,
    }
    return render(request, 'admin_page/update_category.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def update_category2(request, category_id):
    category = Category.objects.get(id=category_id)
    sizes = category.sizes.all()

    if request.method == 'POST':
        for size in sizes:
            size_name  = request.POST.get(str(size.id))
            if size.name != size_name and size_name is not None and size_name != '':
                size.name = size_name
                size.save()

        return redirect(product_management)
    
    sizes_list = sizes.values('id', 'name')

    context = {
        'category': category,
        'sizes' : sizes_list
    }
    return render(request, 'admin_page/update_category2.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def add_product(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_name = request.POST.get('category')
        original_price = request.POST.get('original_price')
        selling_price = request.POST.get('selling_price')
        gender = request.POST.get('gender')
        brand = request.POST.get('brand')
        max_purchase_qty = request.POST.get('max_purchase_qty')
        try:
            original_price = int(original_price)
            selling_price = int(selling_price)
            max_purchase_qty = int(max_purchase_qty)
        except:
            messages.error(request, 'Oops something went wrong.... Kindly try again.')
            return redirect(add_product)

        if selling_price > original_price:
            messages.error(request, 'Orginal Price should be greater than or equal to Selling Price')
            return redirect(add_product)
        
        if max_purchase_qty and (max_purchase_qty > 10 or max_purchase_qty < 1):
            messages.error(request, 'Max purchase quantity should be within 0 and 10')
            return redirect(add_product)

        try:
            category = Category.objects.get(name=category_name)
            seller = User.objects.get(username=(request.user.username))
            product = Product.objects.create(title=title, description=description, category=category, original_price=original_price, selling_price=selling_price, \
                                             gender=gender, brand=brand, created_by= seller,max_purchase_qty = max_purchase_qty, stage = 'stage1')

        except:
            messages.error(request, 'Oops something went wrong')
            return redirect(product_management) 
        
        product.save()
        return redirect(add_product2,product_id=product.id)
    
    categories = Category.objects.filter(is_active=True)
    context = {
        'categories': categories,
    }
    return render(request, 'admin_page/add_product.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def image_saver(request, product_id):
    
    if request.method == 'POST':
        image = request.FILES.get('image')
        product_id = int(product_id)
        product = Product.objects.get(id = product_id)
        product_image = ProductImage.objects.create(product=product, product_image=image)
        product_image.save()
        
        return JsonResponse({'message':'works'})
    else:
        return JsonResponse({'message':'not works'})


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def add_product2(request, product_id):
    product = Product.objects.get(id = product_id)
    if request.method == 'POST':
        selected_colors = request.POST.getlist('colors')
        selected_sizes = request.POST.getlist('sizes')

        for color in selected_colors:
            for size in selected_sizes:
                color_obj = Color.objects.filter(name=color).first()  # incase a color with same name exist
                size_obj = Size.objects.filter(name=size, category = product.category).first()
                variant = ProductVariant.objects.create(product=product, color=color_obj, size=size_obj, quantity = 0)
                variant.save()
        product.stage = 'stage2'
        product.save()
        return redirect(add_product3,product_id=product_id)

    colors = Color.objects.values_list('name', flat=True)
    sizes = product.category.sizes.all()
    
    context = {
        'product_id' : product_id,
        'colors' : colors,
        'sizes' : sizes.values_list('name',flat=True)
    }
    return render(request, 'admin_page/add_product2.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def add_product3(request, product_id):
    product = Product.objects.get(id = product_id)
    variants = product.variants.all()

    if request.method == 'POST':
        
        for variant in variants:
            
            quantity = request.POST.get(str(variant.id))
            if quantity:
                variant.quantity = int(quantity)
            else:
                variant.quantity = 0
            variant.save()
        product.stage = 'stage3'
        product.is_active = True
        product.save()
        messages.success(request, 'Product added successfully')
        return redirect(product_management)
    
    context = {
        'product_id' : product_id,
        'variants': variants,
    }
    return render(request, 'admin_page/add_product3.html', context)


def redirect_add_product(request, product_id):
    try:
        product = Product.objects.get(id = product_id)
        if product.stage == 'stage1':
            return redirect(add_product2, product.id)
        
        elif product.stage == 'stage2':
            return redirect(add_product3, product.id)

    except:
        messages.error(request, 'Oops something went wrong')
        return redirect(product_management)
    return redirect(product_management)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def update_product(request, id):
    product = Product.objects.get(id = id)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        original_price = request.POST.get('original_price')
        selling_price = request.POST.get('selling_price')
        gender = request.POST.get('gender')
        max_purchase_qty = request.POST.get('max_purchase_qty')
        
        try:
            original_price = int(original_price)
            selling_price = int(selling_price)
            max_purchase_qty = int(max_purchase_qty)
        except:
            messages.error(request, 'Oops something went wrong.... Kindly try again.')
            return redirect(update_product, id)

        if selling_price > original_price:
            messages.error(request, 'Orginal Price should be greater than Selling Price')
            return redirect(update_product, id)

        if max_purchase_qty and (max_purchase_qty > 10 or max_purchase_qty < 1):
            messages.error(request, 'Max purchase quantity should be within 0 and 10')
            return redirect(update_product, id)

        changes_detected = False
        if product.title != title and title != None:
            product.title = title
            changes_detected = True

        if product.description != description and description != None:
            product.description = description
            changes_detected = True
        
        if product.selling_price != float(selling_price) and selling_price != None:
            product.selling_price = float(selling_price)
            changes_detected = True
        
        if product.original_price != float(original_price) and original_price != None:
            product.original_price = float(original_price)
            changes_detected = True
        
        if product.gender != gender and gender != None:
            product.gender = gender
            changes_detected = True
        
        if product.max_purchase_qty != int(max_purchase_qty) and max_purchase_qty != None and max_purchase_qty:
            product.max_purchase_qty = max_purchase_qty
            changes_detected = True

        if changes_detected:
            product.save()

        return redirect(update_product2, id) 
        
    context = {
        'product': product,
    }
    return render(request, 'admin_page/update_product.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def update_product2(request, id):
    product = Product.objects.get(id = id)
    product_images = product.product_images.all()
    colors = Color.objects.values_list('name', flat=True)
    sizes = product.category.sizes.values_list('name', flat=True)
    variants_sizes = set(product.variants.values_list('size__name', flat=True))
    variants_colors = set(product.variants.values_list('color__name', flat=True))
    
    if request.method == 'POST':
        selected_colors = request.POST.getlist('colors')
        selected_sizes = request.POST.getlist('sizes')
        all_size = list(variants_sizes) + selected_sizes
       
        if selected_sizes:
            for color in variants_colors:
                for size in selected_sizes:
                    variant = ProductVariant(product=product, color=Color.objects.get(name=color), size=product.category.sizes.get(name=size))
                    variant.save()
        

        if selected_colors:
            for color in selected_colors:
                for size in all_size:
                    variant = ProductVariant(product=product, color=Color.objects.get(name=color), size=product.category.sizes.get(name=size))
                    variant.save()

        for key in request.FILES:
            image = request.FILES[key]
            product_image_obj = product_images.get(id=key)
            product_image_obj.product_image = image
            product_image_obj.save()

        return redirect(update_product3, id)

    context = {
        'product': product,
        'colors': colors,
        'sizes': sizes,
        'product_id': id,
        'product_images': product_images,
        'variants_sizes': variants_sizes,
        'variants_colors': variants_colors,
    }
    return render(request, 'admin_page/update_product2.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def update_product3(request, id):
    product = Product.objects.get(id = id)
    variants = product.variants.all().order_by('quantity')

    if request.method == 'POST':
        for variant in variants:
            quantity = request.POST.get(str(variant.id))

            if quantity != None and quantity != '' and variant.quantity != int(quantity) and not int(quantity) < 0:
                variant.quantity = int(quantity)
                variant.save()

        return redirect(product_management)

    context = {
        'product_id' : id,
        'variants': variants,
    }
    return render(request, 'admin_page/update_product3.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def product_action(request, action, id):
    product = Product.objects.get(id = id)
    if action == 'delete':
        product.is_active = False
        product.save()

    elif action == 'active':
        product.is_active = True
        product.save()
    
    elif action == 'permenentDelete':
        if product.stage != 'stage3':
            product.delete()
            messages.info(request,'Product deleted Permenently')        
        else:
            messages.error(request,'Permenent deletion not possible')        
    return redirect(product_management)

