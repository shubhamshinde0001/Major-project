from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group
from django.dispatch import receiver

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Automatically create default groups after migrations are complete.
    """
    if sender.name == 'core':  # your app name here
        Group.objects.get_or_create(name='conductor')
        Group.objects.get_or_create(name='passenger')
