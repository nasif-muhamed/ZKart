# Generated by Django 5.0.6 on 2024-07-27 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0017_rename_discount_price_coupon_discount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='minimum_amount',
            field=models.FloatField(blank=True, default=500.0, null=True),
        ),
    ]
