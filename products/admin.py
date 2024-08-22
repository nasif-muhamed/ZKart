from django.contrib import admin
from . models import *

# Product and Category related

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Color)
admin.site.register(Size)
admin.site.register(ProductVariant)
admin.site.register(Banner) 
admin.site.register(ProductImage)

