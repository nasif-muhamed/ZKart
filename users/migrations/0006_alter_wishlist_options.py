# Generated by Django 5.0.6 on 2024-07-30 07:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_wishlist'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wishlist',
            options={'ordering': ['-created_at']},
        ),
    ]
