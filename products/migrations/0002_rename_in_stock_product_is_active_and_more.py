# Generated by Django 5.0.6 on 2024-07-12 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='in_stock',
            new_name='is_active',
        ),
        migrations.RemoveField(
            model_name='product',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='product',
            name='small_description',
        ),
        migrations.AlterField(
            model_name='product',
            name='gender',
            field=models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('U', 'Unisex'), ('G', 'General'), ('B', 'Boys'), ('GL', 'Girls')], max_length=2, null=True),
        ),
    ]
