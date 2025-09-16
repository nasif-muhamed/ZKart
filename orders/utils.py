import os
import math
import random
import string
from datetime import datetime
from .models import OrderAddress, Address, Order
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

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

