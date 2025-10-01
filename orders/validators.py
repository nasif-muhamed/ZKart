import re
from .models import Coupon
from django.db.models.functions import Upper, Replace
from django.db.models import Value


def validate_coupon_data(coupon_code=None, description=None, minimum_amount=None, type=None, discount=None):
    if coupon_code:
        coupons = Coupon.objects.annotate(
            lower_name=Upper(Replace('coupon_code', Value(' '), Value('')))
        )
        coupons = coupons.values_list('lower_name', flat=True)

        if coupon_code in coupons:
            return False, "Coupon with similar Coupon Code exists."

        if not re.fullmatch(r"^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]+$", coupon_code):
            return False, "Coupon code can only contain letters, numbers, and special characters."

        if len(coupon_code) < 5:
            return False, "Coupon code must be at least 5 characters long."
        if len(re.findall(r'[a-zA-Z]', coupon_code)) < 3:
            return False, "Coupon code must contain at least 3 alphabets."

    if description:
        if not description or len(description.strip()) < 10:
            return False, "Description must be at least 10 characters long."
        if sum(c.isalpha() for c in description) < 8:
            return False, "Description must contain at least 8 alphabets."

    if minimum_amount:
        try:
            minimum_amount = float(minimum_amount)
        except (TypeError, ValueError):
            return False, "Minimum amount must be a valid number."

        if minimum_amount <= 0:
            return False, "Minimum amount must be greater than 0."
        
    if type:
        valid_types = [choice[0] for choice in Coupon.COUPON_TYPES]
        if type not in valid_types:
            return False, f"Invalid type. Must be one of {', '.join(valid_types)}."

    if discount:
        try:
            discount = float(discount)
        except (TypeError, ValueError):
            return False, "Discount must be a valid number."

        if type == "amount":
            if discount >= minimum_amount:
                return False, "Discount must be less than the minimum amount."
        elif type == "percentage":
            if discount >= 80:
                return False, "Percentage discount cannot be 80 or more."

    return True, None


def validate_create_coupon_data(coupon_code, description, minimum_amount, type, discount):
    if not coupon_code:
        return False, 'Coupone code is required'

    if not description:
        return False, 'Description is required'

    if not minimum_amount:
        return False, 'Minimum amount is required'

    if not type:
        return False, 'Type is required'

    if not discount:
        return False, 'Discount is required'
    
    return validate_coupon_data(coupon_code, description, minimum_amount, type, discount)
