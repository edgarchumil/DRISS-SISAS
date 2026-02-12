import os
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    municipality = models.CharField(max_length=120, blank=True, default="")

    def __str__(self):
        return f"{self.user.username} - {self.municipality}".strip(" -")


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if os.getenv("DISABLE_PROFILE_SIGNAL") == "1":
        return
    if created:
        UserProfile.objects.create(user=instance)
