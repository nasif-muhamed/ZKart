# Generated by Django 5.0.6 on 2024-07-23 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_orderitem_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_charge',
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
    ]
