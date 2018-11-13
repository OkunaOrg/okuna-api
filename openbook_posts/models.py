# Create your models here.
from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Create your views here.
from rest_framework.exceptions import ValidationError

from django.conf import settings
from openbook.storage_backends import S3PrivateMediaStorage
from openbook_auth.models import User

from openbook_common.models import Emoji


class Post(models.Model):
    text = models.CharField(_('text'), max_length=settings.POST_MAX_LENGTH, blank=False, null=True)
    created = models.DateTimeField(editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')

    @classmethod
    def create_post(cls, creator, circles_ids, **kwargs):
        text = kwargs.get('text')
        image = kwargs.get('image')

        if not text and not image:
            raise ValidationError(_('A post requires must have text or an image.'))

        post = Post.objects.create(creator=creator)

        if text:
            post.text = text

        if image:
            PostImage.objects.create(image=image, post_id=post.pk)

        post.circles.add(*circles_ids)

        post.save()

        return post

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Post, self).save(*args, **kwargs)


post_image_storage = S3PrivateMediaStorage() if settings.IS_PRODUCTION else default_storage


class PostImage(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='image')
    image = models.ImageField(_('image'), blank=False, null=False, storage=post_image_storage)


class PostComment(models.Model):
    created = models.DateTimeField(editable=False)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts_comments')
    text = models.CharField(_('text'), max_length=settings.POST_COMMENT_MAX_LENGTH, blank=False, null=False)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostComment, self).save(*args, **kwargs)


class PostReaction(models.Model):
    created = models.DateTimeField(editable=False)
    reactor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    emoji = models.ForeignKey(Emoji, on_delete=models.CASCADE, related_name='reactions')

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostReaction, self).save(*args, **kwargs)
