from django.dispatch import receiver
from django.db.models.signals import post_save

from django_rq import enqueue

from .models import PostVideo
from .helpers import convert_all_videos


@receiver(post_save, sender=PostVideo)
def convert_video(sender, instance, **kwargs):
    enqueue(convert_all_videos,
            instance._meta.app_label,
            instance._meta.model_name,
            instance.pk)
