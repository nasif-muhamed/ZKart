# Generated by Django 5.0.6 on 2024-07-27 10:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0016_coupon_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coupon',
            old_name='discount_price',
            new_name='discount',
        ),
    ]
