import re
from .models import Account
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import date

User = get_user_model()
USERNAME_PATTERN = r'^[a-z0-9_]+$'


def is_password_valid(password):
    if len(password) < 8 or ' ' in password:
        return False
    
    has_lower, has_upper, has_digit, has_symbol = False, False, False, False
    symbols = r'~`!@#$%^&*()_-+={[}]|\:;"\'<,>.?/'

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


def validate_username(value):
    if len(value) < 4:
        return False, "Username must be at least 4 characters long."
    
    if len(value) > 20:
        return False, "Username cannot be longer than 20 characters."
    
    if sum(c.isalpha() for c in value) < 3:
        return False, "Username must contain at least three alphabets."
    
    if not re.match(USERNAME_PATTERN, value):
        return False, "Username must only contain lowercase letters, numbers and underscores."
    
    if User.objects.filter(username__iexact=value).exists():
        return False, "Username is already taken."
    
    return True, None


def validate_name(value):
    return re.match(r"^[A-Za-z\-\' ]+$", value)


def validate_phone_number(value):
    return re.fullmatch(r"\d{10}", str(value))


def validate_pincode(value):
    return re.fullmatch(r"\d{6}", str(value))


def validate_register_data(username, email, pass1, pass2, referral):
    if not all([username, email, pass1, pass2]):
        return False, 'All fields are required.'

    username_validate, username_error = validate_username(username)
    if not username_validate:
        return False, username_error

    if pass1 != pass2:
        return False, "Passwords do not match."

    if not is_password_valid(pass1):
        return False, 'pass_error'

    all_accounts = Account.objects.all()
    if all_accounts.filter(user__email = email).exists():
        return False, 'Email already registered.'

    if referral and not all_accounts.filter(referral_code = referral).exists():
        return False, 'Referral Code not exist.'

    return True, None


def validate_profile_data(first_name, last_name, gender, dob, mobile):
    if first_name is not None:
        if not validate_name(first_name):
            return False, "Invalid first name. Only letters, spaces, hyphens, and apostrophes are allowed."
        if len(first_name) < 2:
            return False, "First name must be at least 2 characters long."

    if last_name is not None:
        if not validate_name(last_name):
            return False, "Invalid last name. Only letters, spaces, hyphens, and apostrophes are allowed."
        if len(last_name) < 2:
            return False, "Last name must be at least 2 characters long."

    if gender is not None:
        valid_genders = [choice[0] for choice in Account.GENDER_CHOICES]
        if gender not in valid_genders:
            return False, f"Invalid gender. Must be one of {', '.join(valid_genders)}."

    if dob is not None:
        if isinstance(dob, str):
            try:
                dob = date.fromisoformat(dob)
            except ValueError:
                return False, "Invalid date format for date of birth. Use YYYY-MM-DD."

        today = now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 12:
            return False, "Age must be at least 12 years."

    if mobile is not None:
        if not validate_phone_number(mobile):
            return False, "Invalid mobile number. Must be exactly 10 digits."

    return True, None


def validate_address_data(name=None, mobile=None, address_line1=None, address_line2=None, city=None, state=None, pin_code=None, country=None):
    if name:
        if not validate_name(name):
            return False, "Invalid name. Only letters, spaces, hyphens, and apostrophes are allowed."
        if len(name) < 2:
            return False, "Name must be at least 2 characters long."

    if mobile and not validate_phone_number(mobile):
        return False, "Invalid mobile number. Must be exactly 10 digits."

    if address_line1 and len(address_line1.strip()) < 5:
        return False, "Address Line 1 must be at least 5 characters long."

    if address_line2 and len(address_line2.strip()) < 3:
        return False, "Address Line 2 must be at least 3 characters long if provided."

    if city and not validate_name(city):
        return False, "Invalid city. Only letters, spaces, and hyphens are allowed."

    if state and not validate_name(state):
        return False, "Invalid state. Only letters, spaces, and hyphens are allowed."

    if pin_code and not validate_pincode(pin_code):
        return False, "Invalid PIN code. Must be exactly 6 digits."

    if country and not validate_name(country):
        return False, "Invalid country. Only letters, spaces, and hyphens are allowed."

    return True, None


def validate_address_creation(name, mobile, address_line1, address_line2, city, state, pin_code, country):
    if not name:
        return False, "Name is required."

    if not mobile:
        return False, "Mobile number is required."

    if not address_line1:
        return False, "Address Line 1 is required."

    if not city:
        return False, "City is required."

    if not state:
        return False, "State is required."

    if not pin_code:
        return False, "PIN code is required."

    if not country:
        return False, "Country is required."

    return validate_address_data(name, mobile, address_line1, address_line2, city, state, pin_code, country)

