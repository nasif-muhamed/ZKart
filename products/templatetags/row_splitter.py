from django import template
from django.utils import timezone

register= template.Library()

@register.filter(name='row_splitter')
def row_splitter(array, limit):
    chunk = []
    count = 0
    for data in array:
        chunk.append(data)
        count += 1
        if count==limit:
            yield chunk
            i=0
            chunk=[]
    if chunk:
        yield chunk


@register.filter(name='split_path') 
def split_path(value):
    return value.strip('/').split('/')


@register.filter(name='get_new_order_quantity')
def get_new_order_quantity(user):
    new_orders = user.account.account_orders.filter(status='cart')
    if new_orders.exists():
        return new_orders.first().get_cart_quantity()
    return 0


@register.filter(name='get_new_order_amount')
def get_new_order_amount(user):
    new_orders = user.account.account_orders.filter(status='cart')
    if new_orders.exists():
        return new_orders.first().get_cart_total()
    return 0


@register.filter(name='has_arrived')
def has_arrived(expected_date):
    if expected_date >= timezone.now():
        return True
    return False


@register.filter(name='length')
def length(value):
    return len(value)


@register.filter(name='getlist')
def getlist(request, key):
    return request.GET.getlist(key)