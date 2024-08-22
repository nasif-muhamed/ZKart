# Generated by Django 5.0.6 on 2024-08-03 17:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_rename_user_wallet_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='referral_code',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='account',
            name='referred_by',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='users.account'),
        ),
    ]
