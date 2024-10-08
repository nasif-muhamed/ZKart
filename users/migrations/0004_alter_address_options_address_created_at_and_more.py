# Generated by Django 5.0.6 on 2024-07-21 10:42

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_address_mobile'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='address',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='address',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_addresses', to='users.account'),
        ),
    ]
