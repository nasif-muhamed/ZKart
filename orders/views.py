import os
import json
import logging
from django.shortcuts import render, redirect
from django.db.models import F, ExpressionWrapper, DateTimeField
from django.db.models.functions import Upper
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, DatabaseError
from .models import *
from .utils import order_address_creator, get_delivery_charge, generate_unique_order_id, render_to_excel, render_to_pdf
from users.models import *
from users.views import *
from users.utils import send_mail
from products.models import *
from products.views import *
from .validators import validate_create_coupon_data, validate_coupon_data

logger = logging.getLogger(__name__)

coords_str = os.getenv("SELLER_HUB_COORDINATES", "9.9312,76.2673")  # Kochi
SELLER_HUB_COORDINATES = tuple(map(float, coords_str.split(",")))
SELLER_MAIL=os.getenv("SELLER_MAIL")
FREE_DELIVERY_LIMIT = int(os.getenv("FREE_DELIVERY_LIMIT_IN_KM") or 100)
DELIVERY_CHARGE_INTERVAL = int(os.getenv("DELIVERY_CHARGE_INTERVAL") or 50)
DELIVERY_PREMIUM_PER_INTERVAL = int(os.getenv("DELIVERY_PREMIUM_PER_INTERVAL") or 20)
COD_LIMIT_IN_INR=int(os.getenv("COD_LIMIT_IN_INR") or 1000)
EXPECTED_ARRIVAL_IN_DAYS=int(os.getenv("EXPECTED_ARRIVAL_IN_DAYS") or 7)

@login_required(login_url='/')
def cart_view(request):
    customer = request.user.account
    order, created = Order.objects.get_or_create(customer=customer, status='cart')
    orders = order.order_items.all()
    sub_total = order.get_cart_total()
    total_discount = order.get_cart_discount()
    coupon_discount = request.session['coupon_discount'] if 'coupon_discount' in request.session else 0
    coupon_applicable = Coupon.objects.filter(is_expired = False)

    if request.method == 'POST' and 'cart_submit' in request.POST:
        request.session['checkout_access'] = True
        return redirect(checkout_page)

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        if 'apply_coupon' in request.POST:
            try:
                coupon = coupon_applicable.get(coupon_code = coupon_code)
                if sub_total > coupon.minimum_amount:
                    request.session['applied_coupon'] = coupon_code

                    if coupon.type == 'amount':
                        request.session['coupon_discount'] = coupon.discount
                    else:
                        request.session['coupon_discount'] = round((sub_total * coupon.discount) / 100)

                    messages.success(request, 'Coupon applied successfully.')

                else:
                    messages.error(request, 'Coupon code not applicable for this order.')

            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid coupon code.')
        
        elif 'remove_coupon' in request.POST:
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

            if 'coupon_discount' in request.session:
                del request.session['coupon_discount']

            messages.info(request, 'Coupon removed successfully.')

        return redirect(cart_view)

    total_amount = sub_total - coupon_discount
    context = {
        'orders' : orders,
        'sub_total' : sub_total,
        'total_discount' : total_discount,
        'total_amount' : total_amount,
        'coupon_applicable' : coupon_applicable,
    }
    return render(request,'cart.html', context)


@login_required(login_url='/')
def add_to_cart(request):
    variant_id = int(request.POST.get('variant_id'))
    quantity = int(request.POST.get('quantity'))
    next_url = request.POST.get('next', None)
    add_success = False

    variant = ProductVariant.objects.get(id = variant_id)
    customer = request.user.account
    logger.info(f"Add to cart attempt: {variant.product.title} (variant: {variant_id}, qty: {quantity}) by {customer.user.username}")

    max_quantity = variant.product.max_purchase_qty
    if quantity > max_quantity:
        logger.warning(f"Add to cart failed - quantity exceeds max purchase limit: {quantity} > {max_quantity}")
        messages.error(request, f'A person can only purchase this product upto {max_quantity} quantity')

    elif quantity > variant.quantity:
        logger.warning(f"Add to cart failed - insufficient stock: {quantity} > {variant.quantity}")
        messages.error(request, 'Insufficient Stock')

    else:
        order, order_created = Order.objects.get_or_create(customer=customer, status='cart')
        order_item, item_created = OrderItem.objects.get_or_create(product_variant = variant, order = order)
        order_item.quantity
        
        if item_created:
            order_item.quantity = quantity
            messages.success(request, 'Product added to cart successfully')
            order_item.save()
            add_success = True
            logger.info(f"Product added to cart successfully: {variant.product.title}")

        else:
            if (order_item.quantity + quantity) > max_quantity:
                logger.warning(f"Cart update failed - quantity exceeds max purchase limit: {order_item.quantity + quantity} > {max_quantity}")
                messages.error(request, f'A person can only purchase this product upto {max_quantity} quantities')

            elif (order_item.quantity + quantity) > variant.quantity:
                logger.warning(f"Cart update failed - insufficient stock: {order_item.quantity + quantity} > {variant.quantity}")
                messages.error(request, 'Insufficient Stock')

            else:
                order_item.quantity += quantity
                messages.success(request, 'Product on cart is updated')
                order_item.save()
                add_success = True
                logger.info(f"Cart updated successfully: {variant.product.title}")

        if add_success:
            if 'coupon_discount' in request.session:
                del request.session['coupon_discount']
                del request.session['applied_coupon']
                messages.info(request, 'Coupon in cart has been reset due to change in order.')

    if next_url:
        return redirect(next_url)
    else:
        return redirect(product_details, variant.product.id)


@login_required(login_url='/')
def update_cart(request):
    data = json.loads(request.body)
    item_id = data['item_id']
    action = data['action']
    order_item = OrderItem.objects.get(id=item_id)

    if action == 'add':
        order_item.quantity = (order_item.quantity + 1)
    
    elif action == 'remove':
        order_item.quantity = (order_item.quantity - 1)

    order_item.save()

    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
        del request.session['applied_coupon']
        # order.coupon = None
        # order.save()
        messages.info(request, 'Coupon has been reset due to change in order.')

    return JsonResponse({'success': True, })     


@login_required(login_url='/')
def delete_cart_item(request):
    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
        del request.session['applied_coupon']
        # order.coupon = None
        # order.save()
        messages.info(request, 'Coupon has been reset due to item removal.')
    
    data = json.loads(request.body)
    item_id = data['item_id']
    item = OrderItem.objects.get(id = int(item_id))
    if item.order.customer != request.user.account:
        return JsonResponse({'success': False, })
    item.delete()
    return JsonResponse({'success': True})     


def get_delivery_charge_for_checkout(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        delivery_charge = get_delivery_charge(address_id)
        return JsonResponse({'delivery_charge': delivery_charge})


@login_required(login_url='/')
def checkout_page(request):
    if request.method == 'GET' and not request.session.get('checkout_access'):
        return redirect(cart_view)
    request.session['checkout_access'] = False

    try:
        customer = request.user.account
        if not customer.is_completed():
            messages.error(request, 'Complete your profile prior to Checkout')
            return redirect(cart_view)

        order = Order.objects.get_or_create(customer=customer, status='cart')[0]
        orders = order.order_items.all()
        if not orders:
            return redirect(cart_view)

        # Validate stock
        for item in orders:
            if item.quantity > item.product_variant.quantity:
                messages.error(request, f"{item.product_variant.product.title} is out of stock")
                return redirect(cart_view)

        addresses = customer.user_addresses.all()
        sub_total = order.get_cart_total()
        coupon_discount = request.session.get('coupon_discount', 0)
        total_amount = sub_total - coupon_discount
        delivery_charge = 'None'

        if request.method == 'POST':
            return handle_checkout_post(
                request, customer, order, orders, addresses, total_amount
            )

        context = {
            'orders': orders,
            'addresses': addresses,
            'sub_total': sub_total,
            'delivery_charge': delivery_charge,
            'total_amount': total_amount,
            'coupon_discount_js': coupon_discount,
        }
        return render(request, 'checkout.html', context)

    except Exception as e:
        logger.exception(f"Checkout error: {e}")
        messages.error(request, 'Something went wrong')
        return redirect(cart_view)


@transaction.atomic
def handle_checkout_post(request, customer, order, orders, addresses, total_amount):
    data = request.POST
    selected_address_id = data.get('selectedAddress')
    selected_payment = data.get('selectedPayment')
    payment_id = data.get('payment_id')
    payment_failed = data.get('payment_failed') == 'true'
    instructions = data.get('special_instructions')

    # Handle payment type
    if 'cod_button' in data:
        selected_payment = 'cod'
        if total_amount > COD_LIMIT_IN_INR:
            messages.error(request, 'Order above ₹1000 not eligible for COD')
            return redirect(cart_view)

    if 'wallet_button' in data:
        selected_payment = 'wallet'
        wallet = customer.wallet
        if wallet.balance < total_amount:
            messages.error(request, 'Not enough balance in Wallet')
            return redirect(cart_view)

    # Validate address
    if not selected_address_id or not selected_payment:
        messages.error(request, 'Select Address and Payment method')
        return redirect(checkout_page)

    address = Address.objects.filter(id=selected_address_id).first()
    delivery_charge = get_delivery_charge(selected_address_id)
    if delivery_charge in ['None', None]:
        messages.error(request, 'Invalid Address')
        return redirect(cart_view)

    # Order setup
    order.address = order_address_creator(address)
    order.payment_method = selected_payment
    order.payment_id = payment_id
    order.special_instructions = instructions or ''
    order.delivery_charge = 0 if delivery_charge == 'Free' else delivery_charge
    order.status = 'pending' if (selected_payment == 'razorpay' and payment_failed) else 'placed'
    order.order_date = timezone.now()
    if selected_payment in ['cod', 'wallet']:
        order.order_identifier = generate_unique_order_id(customer.id)
    order.save()

    process_order_items(order, orders, selected_payment, payment_failed)
    apply_coupon_if_exists(request, order, orders)
    if selected_payment == 'wallet':
        wallet.balance -= total_amount
        wallet.save()

    if selected_payment == 'razorpay':
        return JsonResponse({'status': 'success', 'order_id': order.id})
    return redirect(order_success, order.id)


def process_order_items(order, items, payment_method, payment_failed):
    for item in items:
        item.status = 'pending' if (payment_method == 'razorpay' and payment_failed) else 'in_progress'
        item.order_date = timezone.now()
        item.payment_status = (
            'failed' if (payment_method == 'razorpay' and payment_failed)
            else 'success' if payment_method in ['wallet', 'razorpay']
            else item.payment_status
        )
        item.selling_price = item.product_variant.product.product_selling_price()
        item.original_price = item.product_variant.product.original_price
        item.product_variant.quantity -= item.quantity
        item.product_variant.save()
        item.save()


def apply_coupon_if_exists(request, order, items):
    if 'coupon_discount' not in request.session:
        return
    try:
        order.coupon = Coupon.objects.get(coupon_code=request.session['applied_coupon'])
        total_basic = order.order_total_basic()
        discount_total = int(request.session['coupon_discount'])
        for i in items:
            i.coupon_discount = round((i.selling_price * i.quantity / total_basic) * discount_total)
            i.save()
        order.save()
    finally:
        request.session.pop('applied_coupon', None)
        request.session.pop('coupon_discount', None)

def retry_payment_stock_check(request):
    try:
        order_id = request.POST.get('order_id')
        order = Order.objects.get(id= int(order_id))
        order_identifier = order.order_identifier
        user = request.user
        address = order.address

        if order.status == 'pending' and order.customer.user == request.user:
            for item in order.order_items.all(): 
                if item.quantity > item.product_variant.quantity:
                    return JsonResponse({'status': 'error', 'message': 'Invalid JSON data', 'reason':'Out of stock Items found'}, status=400)

            response_data = {
                'status': 'success',
                'message': f'Your Order ID: {order_identifier}',
                'order_identifier': order_identifier,
                'name': address.name,
                'email': user.email,
                'contact': address.mobile,

            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data', 'reason':'Something went wrong'}, status=400)
    except:
        response_data = {
            'status': 'error',
            'message': f'something went wrong',
            'reason': 'Oops something went wrong',
        }
        return JsonResponse(response_data, status=405)


def retry_payment(request, order_id):
    try:
        payment_id = request.POST.get('payment_id')
        order_identifier = request.POST.get('order_identifier')
        customer = request.user.account
        order = Order.objects.get(customer=customer, order_identifier=order_identifier)
        orders = order.order_items.all()
        order.status = 'placed'
        order.order_date = timezone.now()
        order.payment_id = payment_id
        order.save()

        if orders:
            for order_item in orders:
                order_item.status = 'in_progress'
                order_item.order_date = timezone.now()                    
                order_item.product_variant.quantity -= order_item.quantity
                order_item.payment_status = 'success'
                order_item.save()
                order_item.product_variant.save()
                order_item.product_variant.product.save()

        response_data = {
            'status': 'success',
            'message': f'Your Order ID: {order.id}',
            'order_id': order.id,
        }
        return JsonResponse(response_data)
    
    except:
        response_data = {
            'status': 'error',
            'message': f'something went wrong',
            'order_id': order.id,
        }
        return JsonResponse(response_data)

from zkart.settings import RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY
import razorpay

client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY))
@login_required(login_url='/')
def razorpaycheck(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_address = data.get('selectedAddress')
            address = Address.objects.get(id=int(selected_address))

            user = request.user
            order = Order.objects.get(customer=user.account, status = 'cart')
            sub_total = order.get_cart_total()
            delivery_charge = get_delivery_charge(address.id)
            if delivery_charge == 'Free':
                delivery_charge = 0
            elif  delivery_charge == 'None':
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON data', 'reason':'Invalid Address Add/Select Another one'}, status=400)

            coupon_discount = request.session['coupon_discount'] if 'coupon_discount' in request.session else 0
            total_amount = sub_total + delivery_charge - coupon_discount

            order_currency = 'INR'
            payment_order = client.order.create(dict(amount=total_amount*100, currency=order_currency, payment_capture=1))
            payment_order_id = payment_order['id']

            order.order_identifier = payment_order_id
            order.save()

            response_data = {
                'status': 'success',
                'message': f'Selected address ID: {selected_address}',
                'name': address.name,
                'email': user.email,
                'contact': address.mobile,
                'api_key' : RAZORPAY_API_KEY,
                'order_id' : payment_order_id,
            }
            return JsonResponse(response_data)

        except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required(login_url='/')
def order_success(request, order_id):
    order = Order.objects.get(id= int(order_id))
    if order.order_date:
        expected_arrival = order.order_date + timedelta(days=EXPECTED_ARRIVAL_IN_DAYS)
    else:
        expected_arrival = None

    context = {
        'order' : order, 
        'expected_arrival' : expected_arrival
    }
    return render(request, 'order_success.html', context)


@login_required(login_url='/')
def user_orders_page(request):
    customer = request.user.account
    orders = Order.objects.filter(customer=customer).exclude(status='cart').annotate(
        expected_date=ExpressionWrapper(
            F('order_date') + timedelta(days=7),
            output_field=DateTimeField()
        )
    )

    context = {
        'orders' : orders,
        'account' : customer,
    }
    return render(request,'user_profile/manage_my_order.html', context)
    

@login_required(login_url='/')
def user_order_details(request, order_id):
    customer = request.user.account
    order = Order.objects.get(id=order_id)
    if order.order_date:
        expected_date = order.order_date + timedelta(days=7)
    else:
        expected_date = None

    if 'invoice_btn' in request.GET:
        response = render_to_pdf('user_profile/pdf_invoice.html', {'order':order})
        response['Content-Disposition'] = 'attachment; filename="tax_invoice.pdf"'
        return response

    if request.method == 'POST':
        if 'return_btn' in request.POST:
            order_item_id = request.POST.get('return_btn')
            order_item = OrderItem.objects.get(id=int(order_item_id))
            order_item.return_date = timezone.now()
            # checking return date exceeded or not
            if order_item.return_date > (order_item.order_date + timedelta(days=7)):
                messages.error(request, '7 days return Period is over')
                return redirect(user_order_details, order_id)

            order_item.status = 'return_request'
            order_item.save()

            email = SELLER_MAIL
            mail_subject = f'Return Request of product delivered at {order_item.completed_date.strftime("%Y-%m-%d")}' 
            mail_message = render_to_string('emailer/return_request_email.html', {'order_item': order_item,
                                                                                    'user' : request.user.username,})
            send_mail(email, mail_subject, mail_message)

        elif 'return_cancel_btn' in request.POST:
            order_item_id = request.POST.get('return_cancel_btn')
            order_item = OrderItem.objects.get(id=int(order_item_id))
            order_item.status = 'delivered'
            order_item.save()

        return redirect(user_order_details, order_id)

    context = {
        'order' : order,
        'account' : customer,
        'expected_date': expected_date,
        
    }
    
    return render(request,'user_profile/manage_order_details.html', context)


@login_required(login_url='/')
def user_order_cancel(request, order_item_id):
    try:
        order_item = OrderItem.objects.get(id=int(order_item_id))
        order = order_item.order
        logger.info(f"Order cancellation requested: {order_item.product_variant.product.title} by {request.user.username}")
        
        with transaction.atomic():
            order_item.status = 'cancelled'
            order_item.completed_date = timezone.now()
            order_item.save()
            order_item.product_variant.quantity += order_item.quantity
            if order_item.payment_status == 'success':
                wallet = request.user.account.wallet
                wallet.deposit((order_item.selling_price*order_item.quantity)-order_item.coupon_discount)
                order_item.payment_status = 'wallet'
                wallet.save()
                logger.info(f"Refund processed for cancelled order item: {order_item.id}")
            else:
                order_item.payment_status = 'cancelled'

            if order.is_completed():
                order.complete_date = timezone.now()
                order.status = 'completed'
                order.save()

            order_item.save()
            order_item.product_variant.save()
            order_item.product_variant.product.save()
        
            def send_cancel_email():
                email = SELLER_MAIL
                mail_subject = f'Order Item Cancelled'
                mail_message = render_to_string('emailer/order_cancel_email.html', {'order_item': order_item,
                                                                                    'user' : request.user.username,})
                send_mail(email, mail_subject, mail_message)
                
            transaction.on_commit(send_cancel_email)
            logger.info(f"Order item cancelled successfully: {order_item.id}")

    except Exception as e:
        logger.error(f"Order cancellation failed: {str(e)}")
        print('exception:', e)
        messages.error(request, 'Something went wrong. Cancellation failed. Contact customer care')
    return redirect(user_order_details, order.id)


# Admin side
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def order_management(request):
    orders = Order.objects.exclude(Q(status='cart') | Q(status='pending')).order_by('-order_date')
    search = request.GET.get('search')
    if search and search is not None:
        orders = orders.filter(Q(order_identifier__icontains=search) | Q(customer__user__username__icontains=search) | Q(order_items__status=search))

    context = {
        'orders' : orders,
        'search' : search,
    }
    return render(request,'admin_page/order_management/order_management.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def return_items_management(request):
    return_request = OrderItem.objects.filter(status = 'return_request').order_by('completed_date')
    search = request.GET.get('search')
    if search and search is not None:
        return_request = return_request.filter(Q(order__order_identifier__icontains = search) | Q(product_variant__product__title__icontains=search))
    
    if request.method == 'POST':
        try:
            item_id = request.POST.get('item-id')
            item = return_request.get(id=int(item_id))

            if 'decline-btn' in request.POST and item.status == 'return_request':
                item.status = 'delivered'
                item.save()
                messages.success(request, 'Declined Return Request')

            elif 'accept-btn' in request.POST and item.status == 'return_request':
                item.status = 'returned'
                item.payment_status = 'wallet'
                wallet = item.order.customer.wallet
                wallet.deposit((item.selling_price*item.quantity)-item.coupon_discount) 
                item.product_variant.quantity += item.quantity
                item.save()
                item.product_variant.product.save()
                item.product_variant.save()
                messages.success(request, 'Accepted Return Request')
            
            return redirect(return_items_management)

        except:
            messages.error(request, 'Oops something went wrong')
            return redirect(return_items_management)

    context = {
        'return_request' : return_request,
        'search' : search,
    }
    return render(request,'admin_page/order_management/return_item.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def order_item_management(request, order_id):
    order = Order.objects.get(id = int(order_id))
    order = order.order_items.all()
    context = {
        'order' : order,
    }
    return render(request,'admin_page/order_management/order_item_management.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def update_order_status(request, order_item_id):
    if request.method == 'POST' and request.user.is_staff:
        order_item = OrderItem.objects.get(id=int(order_item_id))
        status = request.POST.get('status')
        order_item.status = status
        order = order_item.order
        logger.info(f"Order status updated by admin {request.user.username}: {order_item.product_variant.product.title} -> {status}")
        
        if status == 'delivered' or status == 'cancelled':
            order_item.completed_date = timezone.now()
            order_item.save()

            if status == 'delivered':
                order_item.payment_status = 'success'
                logger.info(f"Order item delivered: {order_item.id}")

            else:
                order_item.product_variant.quantity += order_item.quantity
                if order_item.payment_status == 'success':
                    wallet = order_item.order.customer.wallet
                    wallet.deposit((order_item.selling_price*order_item.quantity)-order_item.coupon_discount)
                    order_item.payment_status = 'wallet'
                    logger.info(f"Refund processed for cancelled order item: {order_item.id}")
                else:
                    order_item.payment_status = 'cancelled'

                order_item.product_variant.product.save()
                order_item.product_variant.save()

            if order.is_completed():
                order.complete_date = timezone.now()
                order.status = 'completed'
                order.save()
                logger.info(f"Order completed: {order.id}")

        order_item.save()
        return redirect(order_item_management, order.id)
    else:
        return redirect(admin_dashboard)
    

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def admin_coupon_management(request):
    coupons = Coupon.objects.all()
    search = request.GET.get('search')
    if search and search is not None:
        coupons = coupons.filter(Q(coupon_code__icontains=search) | Q(description__icontains=search))
        
    context = {
        'coupons' : coupons,
        'search' : search
    }
    return render(request, 'admin_page/coupon_management/admin_coupon_list.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def add_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        type = request.POST.get('type')
        discount = request.POST.get('discount')

        normalized_code = (coupon_code.upper()).replace(" ", "")
        validate, error = validate_create_coupon_data(normalized_code, description, minimum_amount, type, discount)
        if not validate:
            messages.error(request, error)
            return redirect(add_coupon)
        try:
            Coupon.objects.create(coupon_code=normalized_code, description=description, minimum_amount=float(minimum_amount), type = type, discount=discount)
            messages.success(request, 'Product Addedd Successfully')
        
        except IntegrityError:
            messages.error(request, 'Coupon with same Coupon Code exists')
            return redirect(admin_coupon_management)

        except:
            messages.error(request, 'Oops something went wrong')
            return redirect(admin_coupon_management)
        
        return redirect(admin_coupon_management)
    
    return render(request, 'admin_page/coupon_management/admin_add_coupon.html')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def update_coupon(request, coupon_id):
    coupon = Coupon.objects.get(id=coupon_id)

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        type = request.POST.get('type')
        discount = request.POST.get('discount')
        is_expired = 'is_expired' in request.POST

        normalized_code = (coupon_code.upper()).replace(" ", "")
        # if coupon_code in coupons:
        #     messages.error(request, 'Coupon with similar Coupon Code exists')
        #     return redirect(update_coupon, coupon_id)

        try:
            to_update = {}
            if normalized_code and normalized_code != coupon.coupon_code:
                coupon.coupon_code = normalized_code
                to_update["coupon_code"] = normalized_code
            
            if description and description != coupon.description and description is not None:
                coupon.description = description
                to_update["description"] = description

            if minimum_amount and float(minimum_amount) != coupon.minimum_amount and minimum_amount is not None:
                coupon.minimum_amount = minimum_amount
                to_update["minimum_amount"] = minimum_amount
            
            if type and type != coupon.type and type is not None:
                coupon.type = type
                to_update["type"] = type

            if discount and int(discount) != coupon.discount and discount is not None:
                coupon.discount = int(discount)
                to_update["discount"] = discount

            if is_expired != coupon.is_expired and is_expired is not None:
                coupon.is_expired = is_expired
            
            if discount or minimum_amount or type:
                print('1')
                if not minimum_amount or float(minimum_amount) == coupon.minimum_amount:
                    print('1')
                    to_update["minimum_amount"] = coupon.minimum_amount

                if not discount or int(discount) == coupon.discount:
                    print('1')
                    to_update["discount"] = coupon.discount

                if not type or type == coupon.type:
                    print('1')
                    to_update["type"] = coupon.type

            print('to_update', to_update)
            validate, error = validate_coupon_data(**to_update)
            if not validate:
                messages.error(request, error)
                return redirect(update_coupon, coupon_id)

            if len(to_update):
                coupon.save()
                messages.success(request, 'Coupon Updated Successfully')
            else:
                messages.info(request,'No Changes detected')

            return redirect(admin_coupon_management)
        
        except:
            messages.error(request,'Oops... Something went wrong')
            return redirect(admin_coupon_management)
    
    context = {
        'coupon' : coupon,
    }
    return render(request, 'admin_page/coupon_management/update_coupon.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def sales_report(request):

    def grand_total(order_items):
        return sum(item.item_grand_total() for item in order_items)

    def grand_discount(order_items):
        return sum(item.item_grand_discount() for item in order_items)
    
    time_period = request.GET.get('time_period', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    single_date = request.GET.get('single_date')
    search = request.GET.get('search')

    pdf_button = request.GET.get('pdf_button')
    excel_button = request.GET.get('excel_button')

    order_items = OrderItem.objects.exclude(order__status = 'cart')
    
    if search and search is not None:
        order_items = order_items.filter(
                Q(order__order_identifier__icontains=search) |
                Q(order__customer__user__username__icontains=search) |
                Q(product_variant__product__title__icontains=search)
            )

    if time_period == 'today':
        order_items = order_items.filter(order__order_date__date=date.today())

    elif time_period == 'this_week':
        start_of_week = timezone.now() - timedelta(days=timezone.now().weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        order_items = order_items.filter(order__order_date__gte=start_of_week)

    elif time_period == 'this_month':
        start_of_month = timezone.now().replace(day=1)
        order_items = order_items.filter(order__order_date__gte=start_of_month)

    elif time_period == 'this_year':
        start_of_year = timezone.now().replace(month=1, day=1)
        order_items = order_items.filter(order__order_date__gte=start_of_year)
    
    elif time_period == 'past_7_days':
        past_7_days = timezone.now() - timedelta(days=7)
        order_items = order_items.filter(order__order_date__gte=past_7_days)

    elif time_period == 'by_date' and single_date:
        order_items = order_items.filter(order__order_date__date=single_date)

    elif time_period == 'custom' and start_date and end_date:
        order_items = order_items.filter(order__order_date__date__range=[start_date, end_date])
    
    else:
        time_period = 'all'
        
    if time_period != 'custom':
        start_date = None
        end_date = None

    if time_period != 'by_date':
        single_date = None

    overall_order_items = order_items.count()
    overall_order_amount = grand_total(order_items)
    overall_order_discount = grand_discount(order_items)
    
    success_items = order_items.filter(status = 'delivered')
    overall_success_items = success_items.count()
    overall_success_amount = grand_total(success_items)
    overall_success_discount = grand_discount(success_items)

    cancelled_items = order_items.filter(status = 'cancelled')
    overall_cancelled_items = cancelled_items.count()
    overall_cancelled_amount = grand_total(cancelled_items)
    overall_cancelled_discount = grand_discount(cancelled_items)

    returned_items = order_items.filter(status = 'returned')
    overall_returned_items = returned_items.count()
    overall_returned_amount = grand_total(returned_items)
    overall_returned_discount = grand_discount(returned_items)

    requested_items = order_items.filter(status = 'return_request')
    overall_requested_items = requested_items.count()
    overall_requested_amount = grand_total(requested_items)
    overall_requested_discount = grand_discount(requested_items)

    in_progress_items = order_items.filter(Q(status = 'in_progress') | Q(status = 'shipped'))
    overall_in_progress_items = in_progress_items.count()
    overall_in_progress_amount = grand_total(in_progress_items)
    overall_in_progress_discount = grand_discount(in_progress_items)

    context = {
        'order_items' : order_items,
        'overall_order_items' : overall_order_items,
        'overall_order_amount' : overall_order_amount,
        'overall_order_discount' : overall_order_discount,

        'overall_success_items' : overall_success_items,
        'overall_success_amount' : overall_success_amount,
        'overall_success_discount' : overall_success_discount,

        'overall_cancelled_items' : overall_cancelled_items,
        'overall_cancelled_amount' : overall_cancelled_amount,
        'overall_cancelled_discount' : overall_cancelled_discount,

        'overall_returned_items' : overall_returned_items,
        'overall_returned_amount' : overall_returned_amount,
        'overall_returned_discount' : overall_returned_discount,

        'overall_requested_items' : overall_requested_items,
        'overall_requested_amount' : overall_requested_amount,
        'overall_requested_discount' : overall_requested_discount,

        'overall_in_progress_items' : overall_in_progress_items,
        'overall_in_progress_amount' : overall_in_progress_amount,
        'overall_in_progress_discount' : overall_in_progress_discount,

        'time_period' : time_period,
        'start_date' : start_date,
        'end_date' : end_date,
        'single_date' : single_date,
        'search' : search,
    }

    if pdf_button and pdf_button is not None:
        response = render_to_pdf('admin_page/order_management/pdf_sales_report.html', context)
        response['Content-Disposition'] = 'filename="sales_report.pdf"'
        return response

    if excel_button and excel_button is not None:
        return render_to_excel(order_items, context)

    return render(request, 'admin_page/order_management/sales_report.html', context)


# test
from geopy.geocoders import Nominatim
from geopy import distance
from decimal import Decimal

def test_purpose(request):
    geolocator = Nominatim(user_agent="distance calculation")
    pin_code1, pin_code2 = '676105', 'Aliganj'
    coordinate1 = geolocator.geocode('676105')
    coordinate2 = geolocator.geocode('Aliganj')
    lat1, long1 = (coordinate1.latitude), (coordinate1.longitude)
    lat2, long2 = (coordinate2.latitude), (coordinate2.longitude)
    place1 = (11.075, 76.125) #(lat1, long1)
    place2 = (37.4219999, -122.0840575) #(lat2, long2)
    location = geolocator.reverse("37.4219999, -122.0840575")
    dec = '-123.23456'
    dec = Decimal(dec)
    places = coordinate2, coordinate1
    difference = distance.distance(place1, place2)
    context = {
        'distance': places
    }
    return render(request, 'test_purpose.html', context)

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            client.utility.verify_payment_signature(data)
            return JsonResponse({'status': 'success'})
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'status': 'failed'})

    return JsonResponse({'status': 'failed'})



