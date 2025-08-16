import pyotp
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Custom_user

@receiver(post_save, sender=Custom_user)
def create_otp_secret(sender, instance, created, **kwargs):
    if created and not instance.otp_secret:
        instance.otp_secret = pyotp.random_base32()
        instance.save()