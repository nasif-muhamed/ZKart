from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Account, Wallet


@receiver(pre_save, sender=User)
def check_duplicate_user(sender, instance, **kwargs):
    if instance.pk:
        if User.objects.exclude(pk = instance.pk).filter(email=instance.email).exists():
            raise ValidationError(f"A user with the email {instance.email} already exists.")
        
        if User.objects.exclude(pk = instance.pk).filter(username=instance.username).exists():
            raise ValidationError(f"A user with the username {instance.username} already exists.")
    else:
        if User.objects.filter(email=instance.email).exists():
            raise ValidationError(f"A user with the email {instance.email} already exists.")
        
        if User.objects.filter(username=instance.username).exists():
            raise ValidationError(f"A user with the username {instance.username} already exists.")
        

@receiver(post_save, sender=User)
def creates_related_objects(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "account"):
        account = Account.objects.create(user=instance)
        account.referral_code = account.generate_referral_code()
        account.save()

        Wallet.objects.create(account=account)


from allauth.account.signals import user_signed_up
@receiver(user_signed_up)
def create_account_for_new_user(sender, request, user, **kwargs):
    if not hasattr(user, "account"):
        account = Account.objects.create(user=user)
        account.referral_code = account.generate_referral_code()
        account.save()

        Wallet.objects.create(account=account)
