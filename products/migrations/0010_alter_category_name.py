# Generated by Django 5.0.6 on 2024-08-16 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_category_module_offer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(db_index=True, max_length=250, unique=True),
        ),
    ]
