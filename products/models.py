from django.db import models
from django.conf import settings
import math
from django.db.models import Sum

class Category(models.Model):
    name = models.CharField(max_length=250, unique=True, db_index=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    trending = models.BooleanField(default=False, help_text="0=default, 1=Hidden")
    is_active =  models.BooleanField(default=True)
    module_offer = models.PositiveIntegerField(default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name
    

class Product(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    UNISEX = 'U'
    GENERAL = 'G'
    BOYS = 'B'
    GIRLS = 'GL'

    GENDER_CHOICES = [
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (UNISEX, 'Unisex'),
        (GENERAL, 'General'),
        (BOYS, 'Boys'),
        (GIRLS, 'Girls'),
    ]

    STAGE_CHOICES = [
        ('')
    ]
    title = models.CharField(max_length=250)
    original_price = models.FloatField()
    selling_price = models.FloatField()
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES, null=True, blank=True )
    description = models.TextField(max_length=1000)
    brand = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    trending = models.BooleanField(default=False, help_text="0=default, 1=Hidden")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='product_creator', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_purchase_qty = models.PositiveIntegerField()
    stage = models.CharField(max_length=50, choices=[('stage1', 'Stage1'), ('stage2', 'Stage2'), ('stage3', 'Stage3')])
    
    class Meta:
        ordering = ['-updated_at']


    def __str__(self):
        return self.title
    
    def total_quantity(self):
        return sum(0 if variant.quantity is None else variant.quantity for variant in self.variants.all())
    
    def total_stock_ordered(self):
        all_variants = self.variants.all()
        total = sum([variant.stock_ordered() for variant in all_variants])
        return total
    
    def product_offer(self):
        product_offer = ((self.original_price - self.selling_price) / self.original_price) * 100
        return  round(product_offer)
    
    def offer_percentage(self):
        product_offer = self.product_offer()
        category_offer = self.category.module_offer

        if category_offer and category_offer is not None:
            return round(category_offer) if category_offer > product_offer else product_offer
        return product_offer
    
    def product_selling_price(self):
        category_offer = self.category.module_offer  
        if category_offer and category_offer is not None and self.product_offer() < category_offer:
                price = self.original_price - (self.original_price * category_offer / 100)
                return math.floor(price)
        else:
            return self.selling_price
        
    def orders_recieved(self):
        total_sold = self.variants.filter(ordered_product__status='delivered').aggregate(total_sold=Sum('ordered_product__quantity'))['total_sold']
        return total_sold

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='product_images', on_delete=models.CASCADE)
    product_image = models.ImageField(upload_to='images/')
    def __str__(self):
        return self.product.title


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7)

    def __str__(self):
        return self.name


class Size(models.Model):
    category = models.ForeignKey(Category, related_name='sizes', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    def __str__(self):
        return f'{self.category} + {self.name}'


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=True)

    def __str__(self):
        return f'{self.product} + {self.color} + {self.size} = {self.quantity}'
    
    def quantity_status(self):
        if self.quantity is None:
            status = 'Out of Stock'
        elif self.quantity < 10 and self.quantity > 0:
            status = 'Danger'
        elif self.quantity > 9:
            status = 'In Stock'
        else:
            status = 'Out of Stock'
        return status
    
    def stock_ordered(self):
        order_items = self.ordered_product.all()
        total = sum([item.quantity for item in order_items])
        return total
    

class Banner(models.Model):
    title = models.CharField(max_length=250)
    banner = models.ImageField(upload_to='banners/')
    products = models.ManyToManyField(Product, related_name='banners')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

