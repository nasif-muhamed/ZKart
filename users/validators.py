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
        if not re.match(r"^[A-Za-z\-\' ]+$", first_name):
            return False, "Invalid first name. Only letters, spaces, hyphens, and apostrophes are allowed."
        if len(first_name) < 2:
            return False, "First name must be at least 2 characters long."

    if last_name is not None:
        if not re.match(r"^[A-Za-z\-\' ]+$", last_name):
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
                dob = date.fromisoformat(dob)  # expects "YYYY-MM-DD"
            except ValueError:
                return False, "Invalid date format for date of birth. Use YYYY-MM-DD."

        today = now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 12:
            return False, "Age must be at least 12 years."

    if mobile is not None:
        if not re.fullmatch(r"\d{10}", str(mobile)):
            return False, "Invalid mobile number. Must be exactly 10 digits."

    return True, None
