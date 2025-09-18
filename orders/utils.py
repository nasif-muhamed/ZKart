import os
import math
import random
import string
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import get_template
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from .models import OrderAddress, Address, Order

coords_str = os.getenv("SELLER_HUB_COORDINATES", "9.9312,76.2673")  # Kochi
SELLER_HUB_COORDINATES = tuple(map(float, coords_str.split(",")))
FREE_DELIVERY_LIMIT = int(os.getenv("FREE_DELIVERY_LIMIT_IN_KM") or 100)
DELIVERY_CHARGE_INTERVAL = int(os.getenv("DELIVERY_CHARGE_INTERVAL") or 50)
DELIVERY_PREMIUM_PER_INTERVAL = int(os.getenv("DELIVERY_PREMIUM_PER_INTERVAL") or 20)


def order_address_creator(og_address):
    order_address = OrderAddress()
    order_address.name = og_address.name
    order_address.mobile = og_address.mobile
    order_address.address_line1 = og_address.address_line1
    order_address.address_line2 = og_address.address_line2
    order_address.city = og_address.city
    order_address.state = og_address.state
    order_address.pin_code = og_address.pin_code
    order_address.latitude = og_address.latitude
    order_address.longitude = og_address.longitude
    order_address.country = og_address.country
    order_address.save()
    return order_address


def get_delivery_charge(address_id):
    try:
        address = Address.objects.get(id=address_id)
        address_latitude = address.latitude
        address_longitude = address.longitude
        geolocator = Nominatim(user_agent="zkart")

        if address_latitude is not None and address_longitude is not None:
            user_coordinates = (address_latitude, address_longitude)

        else:
            location = geolocator.geocode(f'{address.city}, {address.pin_code}')

            if location:
                user_coordinates = (location.latitude, location.longitude)
            
            else:
                delivery_charge = 'None'
                return delivery_charge
            
        distance_km = geodesic(SELLER_HUB_COORDINATES, user_coordinates).km

        if distance_km <= FREE_DELIVERY_LIMIT:
            return "Free"
        
        extra_distance = distance_km - FREE_DELIVERY_LIMIT
        intervals = math.ceil(extra_distance / DELIVERY_CHARGE_INTERVAL)
        return intervals * DELIVERY_PREMIUM_PER_INTERVAL
    
    except:
        return 'None'


def generate_unique_order_id(customer_id):
    current_time = datetime.now().strftime('%m%d%H%M%S') 
    customer_id = str(customer_id)
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
    order_id = f"{current_time}{customer_id}{random_chars}"
    order_id = order_id
    
    while Order.objects.filter(order_identifier=order_id).exists():
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
        order_id = f"{current_time}{customer_id}{random_chars}"
        order_id = order_id

    return order_id

import openpyxl
from openpyxl.styles import Font

def render_to_excel(order_items, context):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ZKart Sales Report"

    cell = ws.cell(row=1, column=1, value="ZKart Sales Report")
    cell.font = Font(bold=True)
    ws.cell(row=2, column=1, value="Overall Order Items")
    ws.cell(row=2, column=2, value=context['overall_order_items'])

    ws.cell(row=3, column=1, value="Overall Order Amount")
    ws.cell(row=3, column=2, value=context['overall_order_amount'])

    ws.cell(row=4, column=1, value="Overall Order Discount")
    ws.cell(row=4, column=2, value=context['overall_order_discount'])

    headers = [
        "Order Id", "Username", "Order Item Id", "Order Date",
        "Product Title", "Product Original Price", "Sold Price",
        "Product Quantity", "Product Discount", "Coupon Applied",
        "Coupon Discount", "Total Amount", "Order Item Status",
        "Payment Status", "Payment Method"
    ]
    # Create header row
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col_num, value=header)
        cell.font = Font(bold=True)

    # Add data rows
    for row_num, order_item in enumerate(order_items, 7):
        ws.cell(row=row_num, column=1, value=order_item.order.order_identifier)
        ws.cell(row=row_num, column=2, value=order_item.order.customer.user.username)
        ws.cell(row=row_num, column=3, value=order_item.id)
        if order_item.order.order_date:
            order_date_naive = order_item.order.order_date.replace(tzinfo=None)
            order_date_str = order_date_naive.strftime("%Y-%m-%d")
        else:
            order_date_str = 'N/A'
        ws.cell(row=row_num, column=4, value=order_date_str)
        ws.cell(row=row_num, column=5, value=order_item.product_variant.product.title)
        ws.cell(row=row_num, column=6, value=order_item.original_price)
        ws.cell(row=row_num, column=7, value=order_item.selling_price)
        ws.cell(row=row_num, column=8, value=order_item.quantity)
        ws.cell(row=row_num, column=9, value=order_item.item_discount())
        ws.cell(row=row_num, column=10, value=order_item.order.coupon.coupon_code if order_item.order.coupon else 'N/A')
        ws.cell(row=row_num, column=11, value=order_item.coupon_discount)
        ws.cell(row=row_num, column=12, value=order_item.item_grand_total())
        ws.cell(row=row_num, column=13, value=order_item.status)
        ws.cell(row=row_num, column=14, value=order_item.payment_status)
        ws.cell(row=row_num, column=15, value=order_item.order.payment_method)


    # Save the workbook to a BytesIO object
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=zkart_sales_report.xlsx'
    wb.save(response)
    return response


from xhtml2pdf import pisa
from io import BytesIO

def render_to_pdf(template_src, context_dict): 
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        return response
    return None
