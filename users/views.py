from django.shortcuts import render, redirect, HttpResponse
from . models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db import IntegrityError
from django.urls import reverse
from django.contrib import messages
from products . models import *
from orders . models import *
from django.db.models import F, Sum, Value, FloatField, IntegerField
from django.db.models import Q, Count, Case, When
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models.functions import Coalesce


def user_redirect(request):

    if  not request.user.is_staff:
        return redirect(user_home)
    
    if request.user.is_superuser:
        return redirect(admin_dashboard)

def logout_page(request):
    if request.user.is_staff:
        logout(request)
        return redirect(admin_login)
    logout(request)
    return redirect(login_page)

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def login_page(request):

    context = {
        
    }

    if request.user.is_authenticated:
        redirect_user = user_redirect(request)
        return redirect_user
    
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and not user.is_staff:
            login(request, user)
            return redirect(user_home)
        
        else:
            if Account.objects.filter(user__is_staff= False, user__username= username).exists():
                messages.error(request, 'password is not correct')

            else:
                messages.error(request, 'user does not exist')

            return render(request, 'signin.html', context)
    
    return render(request, 'signin.html', context)

def forgot_password(request):
    context = {
        
    }
    if request.method=='POST':
        email = request.POST.get('email')

        if not Account.objects.filter(user__email = email).exists():
            messages.error(request, 'No account registered with this account.')
            return redirect(forgot_password)
        
        redirect_to = send_otp(request, email)

        return redirect_to

    return render(request, 'otp_verification/forgot_password.html', context) 

import pyotp
from datetime import datetime, timedelta, date

def send_otp(request, email):
    totp = pyotp.TOTP(pyotp.random_base32(), interval=60)
    otp = totp.now()
    
    try:
        mail_subject = 'Forgot Password OTP'
        mail_message = render_to_string('emailer/forgot_otp.html', { 'otp': otp })
        
        emailer = EmailMessage(
            mail_subject, mail_message, to= [email] 
        )
        emailer.send()
        messages.success(request, "Please check your email for OTP. You have one minute to verify OTP")

        request.session['otp_email'] = email
        request.session['otp_secret_key'] = totp.secret
        valid_until = datetime.now() + timedelta(minutes=1)
        request.session['valid_until'] = str(valid_until)
        return redirect(submit_otp)

    except:
        messages.error(request, "Something went wrong while sending OTP.")
        return redirect(forgot_password)


def submit_otp(request, system_otp=''):

    if request.session.get('otp_email') and request.session.get('valid_until') is not None:

        if request.method == 'POST':
            otp = request.POST.get('otp')

            otp_secret_key = request.session['otp_secret_key']
            otp_valid_until = request.session['valid_until']

            if otp_secret_key and otp_valid_until is not None:
                valid_until = datetime.fromisoformat(otp_valid_until) # to change the string to date time obj

                if datetime.now() < valid_until:
                    totp = pyotp.TOTP(otp_secret_key, interval=60)
                    
                    if totp.verify(otp):
                        del request.session['otp_secret_key']
                        del request.session['valid_until']

                        pass_valid_until = datetime.now() + timedelta(minutes=5)
                        request.session['pass_valid_until'] = str(pass_valid_until)
                        messages.success(request, "You have 5 minutes to change your Password")

                        return redirect(change_password)
                    
                    else:
                        messages.error(request, "Invalid OTP")
                        return redirect(submit_otp)
                
                else:
                    del request.session['otp_secret_key']
                    del request.session['valid_until']
                    messages.error(request, "OTP has expired")
                    return redirect(submit_otp)

            else:
                del request.session['otp_secret_key']
                del request.session['valid_until']
                del request.session['otp_email']
                messages.error(request, "oops... something went wrong :)")
                return redirect(forgot_password)

        return render(request, 'otp_verification/submit_otp.html')
    
    return redirect(forgot_password)

def resend_otp(request):

    if request.session.get('otp_email') and request.session.get('valid_until') is not None:
        email = request.session['otp_email']
        redirect_to = send_otp(request, email)
        return redirect_to
    
    return redirect(forgot_password)

def change_password(request):
    
    if request.session.get('otp_email') and request.session.get('pass_valid_until') is not None:
        context = {
            'is_password_valid': False
        }
        if request.method == 'POST':
            pass1 = request.POST.get('password')
            pass2 = request.POST.get('password2')

            if not is_password_valid(pass1):
                context['pass_error'] = True

            elif pass1 != pass2:
                context['is_password_valid'] = True
                messages.error(request, '*password and confirm password is not matching')
            
            else:
                context['is_password_valid'] = True
                pass_valid_until = request.session['pass_valid_until']
                valid_until = datetime.fromisoformat(pass_valid_until) # to change the string to date time obj
                
                if datetime.now() < valid_until:
                    email = request.session.get('otp_email')
                    customer = Account.objects.get(user__email = email)
                    user = customer.user
                    user.set_password(pass1)
                    user.save()
                    customer.save()
                    messages.success(request, 'Your password has successfully changed.')

                else:
                    messages.error(request, 'Session has expired')

                del request.session['pass_valid_until']
                del request.session['otp_email']

                return redirect(login_page)
            
        return render(request, 'otp_verification/change_password.html', context)
    
    return redirect(forgot_password)
        

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from . tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model

def otp_page(request):
    messages_to_display = messages.get_messages(request)
    context = {
        'messages' : messages_to_display
    }
    return render(request, 'signin.html', context)

def register_page(request):
    context = {
        'request': request.method,
    }

    if request.user.is_authenticated:
        redirect_user = user_redirect(request)
        return redirect_user
    
    if request.method == 'POST':
        username= request.POST.get('username')
        email= request.POST.get('email')
        pass1= request.POST.get('password')
        pass2= request.POST.get('repassword')
        referral= request.POST.get('referral')

        if not all([username, email, pass1, pass2]):
            messages.error(request, 'All fields are required.')

        elif not is_password_valid(pass1):
            context['pass_error'] = True
            return render(request, 'signup.html', context)
        
        elif len(username) < 6:
            messages.error(request, '*username must contain atleast 8 charecters')

        elif ' ' in username:
            messages.error(request, '*username should not contain space')

        elif pass1 != pass2:
            messages.error(request, '*password and confirm password is not matching')
        
        elif Account.objects.filter(user__username = username).exists():
            messages.error(request, 'Username already taken.')

        elif Account.objects.filter(user__email = email).exists():
            messages.error(request, 'Email already registered.')

        elif referral and not Account.objects.filter(referral_code = referral).exists():
            messages.error(request, 'Referral Code not exist.')

        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=pass1,
                is_active = False
            )
            customer = Account.objects.create(user=user)
            customer.referral_code = customer.generate_referral_code()
            if referral:
                referrer = Account.objects.get(referral_code=referral)
                referrer.wallet.balance += 100
                customer.referred_by = referrer
                wallet = Wallet.objects.create(account=customer, balance=100)
                referrer.wallet.save()
            else:
                wallet = Wallet.objects.create(account=customer)

            customer.save()

            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            mail_message = render_to_string('emailer/account_activation_email.html', {'user': user,
                                                                                     'domain' : current_site.domain,
                                                                                     'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                                                                                     'token' : account_activation_token.make_token(user)})
            
            emailer = EmailMessage(
                mail_subject, mail_message, to= [email] 
            )
            emailer.send()
            messages.success(request, "Please check your email to complete the registration.")

            return redirect(login_page)

    return render(request, 'signup.html', context)

def activate(request, uidb64, token):
    User = get_user_model()

    try: 
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Your account has been successfully activated")
        return redirect(login_page)
    
    else: 
        messages.error(request, "Activation link is invalid or expired.")
        return redirect(login_page)


# to validate password.
def is_password_valid(password):

    # checking min length and white spice not containing requirment
    if len(password) < 8 or ' ' in password:
        return False
    
    has_lower, has_upper, has_digit, has_symbol = False, False, False, False
    symbols = '~`!@#$%^&*()_-+={[}]|\:;"' "'<,>.?/"
    
    # checking presence of lowercase, uppercase, digit and symbol.
    for character in password:
        if character.islower():
            has_lower = True
        
        if character.isupper():
            has_upper = True
        
        if character.isdigit():
            has_digit = True
        
        if character in symbols:
            has_symbol = True
        
    return has_lower and has_upper and has_digit and has_symbol


def user_home(request):

    products = Product.objects.filter(is_active=True, category__is_active = True, stage = 'stage3').prefetch_related('product_images')

    latest = products.order_by('-created_at')[:5]
    trending = products.annotate(total_stock_ordered=Coalesce(Sum('variants__ordered_product__quantity'), 0)) \
                .order_by('-total_stock_ordered')
    brands = products.values_list('brand', flat=True)
    banners = Banner.objects.all()[:5]
    categories = Category.objects.filter(is_active = True).values_list('name', flat=True)

    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(account = request.user.account).values_list('product', flat=True)

    context = {
        'banners' : banners,
        'latest' : latest,
        'trending' : trending,
        'brands': set(brands),
        'categories': categories,
        'user_wishlist' : user_wishlist,
    }
    return render(request, 'home.html', context)


@login_required(login_url='/')
def user_wishlist(request):
    account = request.user.account
    wishlist = account.wishlists.all()
    
    if request.method == 'POST' and 'remove_btn' in request.POST:
        item_id = request.POST.get('item_id')
        wishlist.get(id=item_id).delete()
        return redirect(user_wishlist)

    context = {
        'account' : account,
        'wishlist' : wishlist,
    }
    return render(request, 'user_profile/wishlist.html', context)


@login_required
def toggle_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = Product.objects.get(id=int(product_id))
        wishlist, created = Wishlist.objects.get_or_create(account=request.user.account, product=product)
        
        if not created:
            wishlist.delete()
            action = 'removed'
        else:
            action = 'added'
        
        return JsonResponse({'action': action})


@login_required(login_url='/')
def user_wallet(request):
    account = request.user.account
    wallet = account.wallet
    history = OrderItem.objects.filter(order__customer=account, payment_status='wallet')
    shopping_history = Order.objects.filter(customer=account, payment_method = 'wallet')
    context = {
        'account' : account,
        'wallet' : wallet,
        'history': history,
        'shopping_history' : shopping_history,
    }
    return render(request, 'user_profile/user_wallet.html', context)


@login_required(login_url='/')
def user_referral(request):
    referrals = request.user.account.referrals.all()
    total_earned = len(referrals) * 100
    
    context = {
        'referrals' : referrals,
        'total_earned' : total_earned,
    }
    return render(request, 'user_profile/user_referral.html', context)


@login_required(login_url='/')
def user_profile(request):

    if request.user.is_authenticated and not request.user.is_staff:
        account = Account.objects.get(user= request.user)
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            gender = request.POST.get('gender')
            dob = request.POST.get('dob')
            mobile = request.POST.get('mobile')
            
            changes = False
            user = account.user
            if first_name != user.first_name or last_name != user.last_name:
                if first_name != user.first_name and first_name:
                    user.first_name = first_name

                if last_name != user.last_name and last_name:
                    user.last_name = last_name
                
                changes = True


            if gender != account.gender or dob != str(account.dob) or mobile != account.phone_number:
                if gender != account.gender and gender:
                    account.gender = gender

                if dob != str(account.dob) and dob:
                    account.dob = dob
                
                if mobile != account.phone_number and mobile:
                    account.phone_number = mobile

                changes = True

            try:
                # put it into if changes: after review 
                user.save()
                account.save()
                if changes:
                    messages.success(request, 'Profile updated successfully.')

            except ValidationError as e:
                messages.error(request, str(e))
                return redirect(user_profile)  

            return redirect(user_profile)
            
        context ={
            'account' : account
        }
        return render(request, 'user_profile/user_profile.html', context)
    
    return redirect(user_home)

from decimal import Decimal
@login_required(login_url='/')
def address_management(request):

    if request.user.is_authenticated and not request.user.is_staff:
        account = Account.objects.get(user= request.user)
        addresses = Address.objects.filter(account=account)
        
        if request.method == 'POST':
            name = request.POST.get('name')
            mobile = request.POST.get('mobile')
            address_line1 = request.POST.get('address_line1')
            address_line2 = request.POST.get('address_line2')
            city = request.POST.get('city')
            state = request.POST.get('state')
            pin_code = request.POST.get('pin_code')
            country = request.POST.get('country')
            default = 'default' in request.POST
            next_url = request.POST.get('next', '/')
            checkout_access = request.POST.get('checkout_access')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if latitude is not None and longitude is None:
                latitude, longitude = Decimal(latitude), Decimal(longitude)

            if default and len(addresses)>0:
                previous = addresses.get(default=True) 
                previous.default = False
                previous.save()

            if not default and not len(addresses):
                default = True

            new_address = Address(account=account, name=name, mobile=mobile, address_line1=address_line1, address_line2=address_line2, \
                                  city=city, state=state, pin_code=pin_code, country=country, default=default, latitude=latitude, longitude=longitude)
            
            new_address.save()
            messages.success(request, 'Address added successfully')

            if checkout_access:
                request.session['checkout_access'] = True
                
            return redirect(next_url)
        
        if len(addresses) > 0:
            try:
                default_address = addresses.get(default=True)
            except:
                new = addresses.filter(default = False).first()
                new.default = True
                new.save()
                default_address = new

        else:
            default_address = None

        context ={
            'account' : account,
            'default_address' : default_address,
            'addresses' : addresses.exclude(default=True),
        }
        return render(request, 'user_profile/manage_address.html', context)
    
    return redirect(user_home)


@login_required(login_url='/')
def get_address_details(request, address_id):
    address = Address.objects.get(id=address_id)
    address_data = {
        'name': address.name,
        'mobile': address.mobile,
        'address_line1': address.address_line1,
        'address_line2': address.address_line2,
        'city': address.city,
        'state': address.state,
        'pin_code': address.pin_code,
        'country': address.country,
        'default' : address.default,
    }
    return JsonResponse(address_data)

@login_required(login_url='/')
def edit_address(request, address_id):
    address = Address.objects.get(id=address_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pin_code = request.POST.get('pin_code')
        country = request.POST.get('country')
        default = 'default' in request.POST
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        if latitude and longitude and latitude is not None and longitude is not None:
            latitude, longitude = Decimal(latitude), Decimal(longitude)
            
        update = False
        if address.name != name and name:
            address.name = name
            update = True

        if address.mobile != mobile and mobile:
            address.mobile = mobile
            update = True
        
        if address.address_line1 != address_line1 and address_line1:
            address.address_line1 = address_line1
            update = True

        if address.address_line2 != address_line2 and address_line2:
            address.address_line2 = address_line2
            update = True

        if address.city != city and city:
            address.city = city
            update = True

        if address.state != state and state:
            address.state = state
            update = True

        if address.pin_code != pin_code and pin_code:
            address.pin_code = pin_code
            address.latitude = latitude
            address.longitude = longitude
            update = True

        if address.country != country and country:
            address.country = country
            update = True

        if address.default != default and default:
            previous = Address.objects.get(account=request.user.account, default=True)
            previous.default = False
            previous.save()
            address.default = True
            update = True

        if update:
            address.save()
            messages.success(request, 'Address updated successfully.')
        else:
            messages.info(request, 'No edits found.')
            
        return redirect(address_management)
    
    return redirect(address_management)

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

@login_required(login_url='/')
@csrf_protect
@require_http_methods(["DELETE"])
def delete_address(request, address_id):
    try:
        # Find the address by ID
        account = request.user.account
        addresses = Address.objects.filter(account=account)
        address = addresses.get(id=address_id)

        # set new one as default
        if address.default and len(addresses) > 1:
            new = addresses.filter(default = False).first()
            new.default = True
            new.save()

        # Delete the address
        address.delete()
        messages.success(request, 'address deleted')
        return JsonResponse({'success': True}, status=200)
    
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Address not found.'}, status=404)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required(login_url='/')
def reset_password(request):
    account = Account.objects.get(user= request.user)

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        repeat_password = request.POST.get('repeat_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Entered password does not matching with your previous password.')
        
        elif not is_password_valid(new_password):
            messages.error(request, "password must contain atleast 8 charecters a lower case an upper case, \
                                    a digit and a special character and it should not contain any white space ")

        elif new_password != repeat_password:
            messages.error(request, 'New password and repeat password do not match.')

        elif new_password == current_password:
            messages.error(request, 'New password is same as previous password.')

        else:  
            user = request.user
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Your password has been updated successfully.')

            user = authenticate(username=user.username, password=new_password)
            if user is not None:
                login(request, user)

            else:
                messages.error(request, 'New password is same as previous password.')
                return redirect(login_page)

            return redirect(user_profile)

    context = { 
        'account' : account,
    }
    return render(request, 'user_profile/reset_password.html', context)


# admin 
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.is_staff

def permission_denied_view(request):
    return render(request, 'permission_denied.html')


def admin_login(request):
    context={
        'admin':True
    }

    if request.user.is_authenticated:
        redirect_user = user_redirect(request)
        return redirect_user
    
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect(admin_dashboard)
        
        else:
            if User.objects.filter(username=username, is_staff=True).exists():
                messages.error(request, 'password is not correct')

            else:
                messages.error(request, 'user does not exist')


    return render(request, 'signin.html', context)

from . charts import *

from django.db.models.functions import TruncDate, TruncMonth, TruncYear
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def admin_dashboard(request):
    chart_filter = request.GET.get('filter', 'daily')

    order_items = OrderItem.objects.exclude(status__in= ['cart', 'pending'])
    active_users = Account.objects.filter(user__is_active = True)
    active_products = Product.objects.filter(is_active = True)
    
    def grand_total(order_items):
        return sum(item.item_grand_total() for item in order_items)

    overall_order_items = order_items.count()
    
    success_items = order_items.filter(status = 'delivered')
    overall_success_items = success_items.count()
    overall_success_amount = grand_total(success_items)

    cancelled_items = order_items.filter(status = 'cancelled')
    overall_cancelled_items = cancelled_items.count()

    returned_items = order_items.filter(status = 'returned')
    overall_returned_items = returned_items.count()

    requested_items = order_items.filter(status = 'return_request')
    overall_requested_items = requested_items.count()

    in_progress_items = order_items.filter(Q(status = 'in_progress') | Q(status = 'shipped'))
    overall_in_progress_items = in_progress_items.count()

    failed_items = OrderItem.objects.filter(status = 'pending')
    overall_failed_items = failed_items.count()

    order_daily = order_items.annotate(order_filter=TruncDate('order_date'))
    orders_for_chart_filter = order_daily
    date_format = '%d-%m-%y'
    
    if chart_filter == 'monthly':
        order_monthly = order_items.annotate(order_filter=TruncMonth('order_date'))
        orders_for_chart_filter = order_monthly
        date_format = '%B'

    elif chart_filter == 'yearly':
        order_yearly = order_items.annotate(order_filter=TruncYear('order_date'))
        orders_for_chart_filter = order_yearly
        date_format = '%Y'

    orders_for_chart = orders_for_chart_filter.values('order_filter').order_by('-order_filter')

    chart_sales = orders_for_chart.filter(status='delivered').annotate( total_sales=Sum(F('selling_price')) )[:10]
    labels_sales = [order['order_filter'].strftime(date_format) for order in chart_sales]
    data_sales = [order['total_sales'] for order in chart_sales]
    sales_chart = BarChartSingle("rgba(0, 0, 0, 0.8)", 'Sales' ,labels_sales, data_sales)
    sales_chart_json = sales_chart.get()

    chart_orders = orders_for_chart.annotate(order_count=Count('id'))[:10]
    labels_orders = [order['order_filter'].strftime(date_format) for order in chart_orders]
    data_orders = [order['order_count'] for order in chart_orders]
    orders_chart = BarChartSingle("rgba(59, 113, 202, .9)", 'Orders' ,labels_orders, data_orders)
    orders_chart_json = orders_chart.get()

    chart_orders_status = orders_for_chart.annotate(
        delivered_count=Count(Case(When(Q(status='delivered') | Q(status='return_request'), then=1))),
        in_progress_count=Count(Case(When(Q(status='in_progress') | Q(status='shipped'), then=1))),
        returned_cancelled=Count(Case(When(Q(status='returned') | Q(status='cancelled'), then=1))),
    )[:10]
    labels_orders_status = [order['order_filter'].strftime(date_format) for order in chart_orders_status]
    success_data = [order['delivered_count'] for order in chart_orders_status]
    progress_data = [order['in_progress_count'] for order in chart_orders_status]
    return_data = [order['returned_cancelled'] for order in chart_orders_status]
    
    chart = BarChartOrderStatus(labels_orders_status, success_data, progress_data, return_data)
    chart_json = chart.get()

    top_10_brands = (
        Product.objects.filter(variants__ordered_product__status='delivered')
        .values('brand')  # Group by brand
        .annotate(total_sold=Sum('variants__ordered_product__quantity'))
        .order_by('-total_sold')[:10]
    )
    brand_labels = [brand['brand'] for brand in top_10_brands]
    brand_data = [brand['total_sold'] for brand in top_10_brands]

    top_10_categories = (
        Product.objects.filter(variants__ordered_product__status='delivered')
        .values('category__name')
        .annotate(total_sold=Sum('variants__ordered_product__quantity'))
        .order_by('-total_sold')[:10]
    )
    category_labels = [category['category__name'] for category in top_10_categories]
    category_data = [category['total_sold'] for category in top_10_categories]
    
    top_10_selling_products = (
    Product.objects.filter(variants__ordered_product__status='delivered')
    .annotate(total_sold=Sum('variants__ordered_product__quantity'))
    .order_by('-total_sold')[:10]
    )
    
    top_buyers = (
        Account.objects.annotate(
            total_items=Coalesce(Sum('account_orders__order_items__quantity', filter=Q(account_orders__order_items__status='delivered'),output_field=IntegerField()), Value(0)), 
            total_spent=Coalesce(Sum(
                (F('account_orders__order_items__selling_price') * F('account_orders__order_items__quantity') - F('account_orders__order_items__coupon_discount')),
                filter=Q(account_orders__order_items__status='delivered'),output_field=IntegerField()), Value(0))
        )
        .order_by('-total_spent')[:10]
    )

    context = {
        'total_revenue' : overall_success_amount,
        'total_orders' : overall_order_items,
        'active_users' : active_users.count(),
        'total_products' : active_products.count(),
        'delivered' : overall_success_items,
        'progress' : overall_in_progress_items,
        'cancelled' : overall_cancelled_items,
        'returned': overall_returned_items,
        'requested' : overall_requested_items,
        'failed' : overall_failed_items,
        'chart': chart_json,
        'orders_chart' : orders_chart_json,
        'sales_chart' : sales_chart_json,
        'chart_filter' : chart_filter,
        'brand_labels': brand_labels,
        'brand_data': brand_data,
        'category_labels' : category_labels,
        'category_data' : category_data,
        'top_buyers' : top_buyers,
        'top_10_selling_products' : top_10_selling_products,
    }
    return render(request, 'admin_page/dashboard.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def user_management(request):

    if request.user.is_authenticated and not request.user.is_staff:
        redirect_user = user_redirect(request)
        return redirect_user
    
    users = Account.objects.filter(user__is_staff = False)
    user_search = request.GET.get('user_search')
    if user_search and user_search is not None:
        users = users.filter(Q(user__username__icontains=user_search) | Q(user__email__icontains=user_search))

    active_users = users.filter(user__is_active = True)
    deleted_users = users.filter(user__is_active = False)

    context = {
        'active_users' : active_users,
        'deleted_users': deleted_users,
        'user_search' : user_search,
    }
    return render(request, 'admin_page/user_management.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='/permission-denied/')
def user_action(request, action, id):
    costomer = Account.objects.get(id = id)
    user = costomer.user
    if action == 'delete':
        user.is_active = False
        user.save()

    elif action == 'active':
        user.is_active = True
        user.save()
    
    costomer.save()
    return redirect(user_management)
