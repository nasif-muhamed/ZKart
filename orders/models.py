from django.db import models
from users . models import *
from products . models import *
import uuid


class OrderAddress(models.Model):
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

    def __str__(self):
        return f"{self.name}, {self.address_line1}, {self.city}, {self.state}, {self.country}"
    

class Coupon(models.Model):
    COUPON_TYPES = [
        ('percentage', 'Percentage'),
        ('amount', 'Amount'),
    ]

    coupon_code = models.CharField(max_length=50, unique=True)
    is_expired = models.BooleanField(default=False)
    discount = models.PositiveIntegerField(default=100)
    minimum_amount = models.FloatField(default=500.0, null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)
    type = models.CharField(max_length=50, choices=COUPON_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.coupon_code
    
    class Meta:
        ordering = ['is_expired','-created_at']


class Order(models.Model):
    CUSTOMER_CHOICES = (
        ('cart', 'Cart'),
        ('deleted', 'Order Deleted'),
        ('placed', 'Order Placed'),
        ('completed', 'Order Completed'),
        ('cancelled', 'Order Cancelled'),
        ('pending', 'Pending'),
    )

    PAYMENT_CHOICES = (
        ('cod', 'Cash On Delivery'),
        ('paypal', 'PayPal'),
        ('razorpay', 'RazorPay'),
        ('wallet', 'Wallet'),
    )

    customer = models.ForeignKey(Account, related_name='account_orders', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(default='cart', max_length=50, choices=CUSTOMER_CHOICES)
    order_identifier = models.CharField(max_length=100, editable=True, null=True, blank=True) #unique=True
    address = models.ForeignKey(OrderAddress, related_name='order_address', on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(null=True, blank=True)
    complete_date = models.DateTimeField(null=True, blank=True)
    total_amount = models.FloatField(default=0.0, null=True, blank=True)
    delivery_charge = models.FloatField(default=0.0, null=True, blank=True)
    total_discount = models.FloatField(default=0.0, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True, choices=PAYMENT_CHOICES)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    special_instructions = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.customer.user.username} + {self.status} + {self.id}'
    
    class Meta:
        ordering = ['-created_at']
    
    def get_cart_total(self):
        order_items = self.order_items.all()
        total = sum([item.get_total() for item in order_items])
        return total
    
    def get_cart_discount(self):
        order_items = self.order_items.all()
        total = sum([item.get_discount() for item in order_items])
        return total
    
    def get_cart_quantity(self):
        order_items = self.order_items.all()
        total = sum([item.quantity for item in order_items])
        return total 
    
    def order_total_basic(self):
        order_items = self.order_items.all()
        total = sum([item.selling_price*item.quantity for item in order_items])
        return total

    def coupon_discount(self):
        order_items = self.order_items.all()
        total_coupon_discount = sum([item.coupon_discount for item in order_items])
        return total_coupon_discount

    def order_total_amount(self):
        order_items = self.order_items.all()
        total = sum([(item.selling_price)*item.quantity for item in order_items])
        return total + self.delivery_charge - self.coupon_discount()
    
    def order_total_saved(self):
        order_items = self.order_items.all()
        total = sum([(item.original_price - item.selling_price)*item.quantity for item in order_items])
        return total + self.coupon_discount()

    def order_payment_status(self):
        order_items = self.order_items.all()
        result = []
        for i in order_items:
            result.append(i.payment_status)

        return False if 'pending' in result or 'pending' in result or 'cancelled' in result  else True
    
    def is_completed(self):
        order_items = self.order_items.all()
        for item in order_items:
            if not item.completed_date:
                return False
        return True
    

class OrderItem(models.Model):
    SELLER_CHOICES = (
        ('cart', 'Cart'),
        ('in_progress', 'In Progress'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('return_request', 'Requested for Return'),
        ('returned', 'Returned'),
        ('pending', 'Pending'),
    )
    
    PAYMENT_ABOUT= (
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('success', 'Success'),
        ('cancelled', 'Cancelled'),
        ('wallet', 'Added to Wallet'),
    )

    product_variant = models.ForeignKey(ProductVariant, related_name='ordered_product', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0, null=True, blank=True)
    status = models.CharField(max_length=50, default='cart', choices=SELLER_CHOICES, null=True, blank=True)
    selling_price = models.FloatField(default=0.0, null=True, blank=True)
    original_price = models.FloatField(default=0.0, null=True, blank=True)
    coupon_discount = models.FloatField(default=0.0, null=True, blank=True)
    # delivery_charge_deduction = models.FloatField(default=None, null=True, blank=True)
    subtotal = models.FloatField(default=0.0, null=True, blank=True)
    order_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(max_length=50, default='pending', choices=PAYMENT_ABOUT, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product_variant.product.title} + {str(self.quantity)} + {self.order}'
    
    def get_total(self):
        product_selling_price = self.product_variant.product.product_selling_price()
        return product_selling_price  * self.quantity

    def get_discount(self):
        product_difference = self.product_variant.product.original_price - self.product_variant.product.product_selling_price()
        discount = product_difference * self.quantity
        return discount
    
    def get_discount_percentage(self):
        discount_percentage = self.product_variant.product.offer_percentage()
        return round(discount_percentage)

    def item_discount(self):
        discount = (self.original_price - self.selling_price) * self.quantity
        return discount
    
    def item_total(self):
        total = (self.selling_price * self.quantity)
        return total
    
    def item_grand_total(self):
        total = (self.selling_price * self.quantity) - self.coupon_discount
        return total
    
    def item_grand_discount(self):
        discount = self.item_discount() + self.coupon_discount
        return discount

