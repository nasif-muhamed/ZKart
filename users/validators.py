import re
from .models import Account
from django.contrib.auth import get_user_model

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