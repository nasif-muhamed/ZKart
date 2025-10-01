import re
from django.db.models.functions import Lower, Replace
from django.db.models import Value
from .models import Category, Product

NAME_PATTERN = r"^[A-Za-z\-\' ]+$"


def validate_name(value):
    return re.match(NAME_PATTERN, value)


def get_all_categories():
    return Category.objects.filter(is_active=True).values_list('name', flat=True)


def get_all_product_titles():
    return Product.objects.annotate(
        lower_title=Lower(Replace('title', Value(' '), Value('')))
    ).values_list('lower_title', flat=True)


def validate_category_data(name=None, is_active=None, module_offer=None):
    if name:
        if not validate_name(name):
            return False, "Invalid name. Only letters, spaces, hyphens, and apostrophes are allowed."
        if len(name) < 3:
            return False, "Name must be at least 3 characters long."
        if len(re.findall(r'[a-zA-Z]', name)) < 3:
            return False, "Name must contain at least 3 alphabets."

        categories = Category.objects.annotate(lower_name = Lower(Replace('name', Value(' '), Value('')))).values_list('lower_name', flat=True)
        category_check = (name.lower()).replace(" ", "")
        if category_check in categories:
            return False, "Category with similar title exists."

    if is_active is not None and not isinstance(is_active, bool):
        return False, "Invalid type for is active field."
    
    if module_offer is not None:
        try:
            module_offer = float(module_offer)
            if module_offer < 0:
                return False, "Offer must be a valid positive integer."
            if module_offer >= 90:
                return False, "Offer must be lesser than 90%."
            
        except (TypeError, ValueError):
            return False, "Offer must be a valid integer."

    return True, None


def validate_create_category_data(name, is_active, module_offer):
    if not name:
        return False, "Title is required"
    if not isinstance(is_active, bool):
        return False, "Active field is required"
    return validate_category_data(name, is_active, module_offer)


def validate_size(size_name, sizes):
    sizes_names = sizes.annotate(
        lower_name=Lower(Replace('name', Value(' '), Value('')))
    ).values_list('lower_name', flat=True)
    size_name = (size_name.lower()).replace(" ", "")

    if size_name in sizes_names:
        return False, 'Similar Size is already added'
    
    if not re.fullmatch(r'^[A-Za-z0-9]+$', size_name):
        return False, 'Size must contain only letters and numbers'

    if len(size_name) > 2:
        return False, 'Size can only contain 2 Characters'
    return True, None


def validate_product_data(title=None, description=None, category_name=None, original_price=None, selling_price=None, gender=None, brand=None, max_purchase_qty=None):
    try:
        if title:
            if len(title.strip()) < 10:
                return False, "Title must be at least 10 characters long."
            if len(re.findall(r'[a-zA-Z]', title)) < 8:
                return False, "Title must contain at least 8 alphabetic characters."
            print(title, get_all_product_titles())
            title = (title.lower()).replace(" ", "")
            if title in get_all_product_titles():
                return False, "Similar Product title exists"
        
        if description:
            if len(description.strip()) < 30:
                return False, "Description must be at least 15 characters long."
            if len(re.findall(r'[a-zA-Z]', description)) < 15:
                return False, "Description must contain at least 15 alphabetic characters."
            
        if category_name and category_name not in get_all_categories():
            return False, "Select a valid category"
        
        try:
            if original_price and selling_price:
                original_price = float(original_price)
                selling_price = float(selling_price)
                if selling_price < 1 or original_price < 1:
                    return False, "Price must be positive."

                if original_price < selling_price:
                    return False, "Selling price must be lesser than original price."

        except (TypeError, ValueError):
            return False, "Prices must be valid numbers."

        if gender:
            valid_genders = [choice[0] for choice in Product.GENDER_CHOICES]
            if gender not in valid_genders:
                return False, "Select a valid gender"
        
        if brand: 
            if len(brand.strip()) < 3:
                return False, "Brand name must be at least 3 characters long."
            if len(re.findall(r'[a-zA-Z]', title)) < 2:
                return False, "Brand name must contain at least 2 alphabetic characters."
        
        if max_purchase_qty:
            print('inside max purchase')
            try:
                max_purchase_qty = int(max_purchase_qty)
                if max_purchase_qty <= 0:
                    return False, "Max purchase quantity must be greater than 0."
                if max_purchase_qty > 10:
                    return False, "Max purchase quantity cannot exceed 10."
            except (TypeError, ValueError):
                return False, "Max purchase quantity must be an integer."
    
    except Exception as e:
        return False, "Something went wrong. Try again."
    
    return True, None


def validate_create_product_data(title, description, category_name, original_price, selling_price, gender, brand, max_purchase_qty):
    print('inside 1:', title, description, category_name, original_price, selling_price, gender, brand, max_purchase_qty)
    if not title:
        return False, "Title is required"
    if not description:
        return False, "Description is required"
    if not category_name:
        return False, "Category is required"
    if not original_price:
        return False, "Original Price is required"
    if not selling_price:
        return False, "Selling Price is required"
    if not gender:
        return False, "Gender is required"
    if not brand:
        return False, "Brand is required"
    if not max_purchase_qty:
        return False, "Purchase Quantity is required"
    
    return validate_product_data(title, description, category_name, original_price, selling_price, gender, brand, max_purchase_qty)
