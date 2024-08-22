from . models import OrderItem


def return_request_count(request):
    count = OrderItem.objects.filter(status = 'return_request').count()
    return {'return_request_count': count}