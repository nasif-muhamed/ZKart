# Generated by Django 5.0.6 on 2024-07-14 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_remove_product_product_image_productimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariant',
            name='quantity',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
