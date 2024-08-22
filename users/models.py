from django.db import models
from django.contrib.auth.models import User
from products.models import *
import random
import string


class Account(models.Model):

    MALE = 'Male'
    FEMALE = 'Female'
    GENDER_CHOICES = [
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='user_profile/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True )
    dob = models.DateField(null=True, blank=True)
    referral_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')

    # Usual fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f'{self.user.username}, {self.created_at}' 
    
    def is_completed(self):
        # for checking profile info is filled or not
        if self.user.first_name and  self.user.last_name and self.phone_number and self.gender and self.dob:
            return True
        return False
    
    def generate_referral_code(self):
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        random_digits = ''.join(random.choices(string.digits, k=2))
        return f"{self.id}{self.user.username[:5].upper()}{random_letters}{random_digits}"


class Wallet(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='wallet')
    balance = models.FloatField(default=0.0,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account}'s Wallet"

    def deposit(self, amount):
        self.balance += amount
        self.save()

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False



class Address(models.Model):
    account = models.ForeignKey(Account, related_name="user_addresses", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    country = models.CharField(max_length=100)
    default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"{self.name}, {self.pin_code}, {self.city}, {self.state}, {self.country}, {self.account.user.username}, default:{self.default}"

    class Meta:
        ordering = ['-created_at']


class Wishlist(models.Model):
    account = models.ForeignKey(Account, related_name="wishlists", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.user.username} - {self.product.title[:10]}"
    
    class Meta:
        ordering = ['-created_at'] 


