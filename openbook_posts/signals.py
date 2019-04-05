from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import enqueue

from video_encoding import tasks

from .models import Video


@receiver(post_save, sender=Video)
def convert_video(sender, instance, **kwargs):
    enqueue(tasks.convert_all_videos,
            instance._meta.app_label,
            instance._meta.model_name,
            instance.pk)
