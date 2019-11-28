from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone

# Create your models here.
from django.utils.translation import ugettext_lazy as _
from imagekit.models import ProcessedImageField
from pilkit.processors import ResizeToFit

from openbook.storage_backends import S3PrivateMediaStorage
from openbook_common.utils.helpers import generate_random_hex_color, delete_file_field
from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community
from openbook_hashtags.helpers import upload_to_hashtags_directory
from openbook_posts.models import Post

hashtag_image_storage = S3PrivateMediaStorage() if settings.IS_PRODUCTION else default_storage


class Hashtag(models.Model):
    name = models.CharField(_('name'), max_length=settings.HASHTAG_NAME_MAX_LENGTH, blank=False, null=False,
                            unique=True)
    color = models.CharField(_('color'), max_length=settings.COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    created = models.DateTimeField(editable=False)
    posts = models.ManyToManyField(Post, related_name='hashtags')
    width = models.PositiveIntegerField(editable=False, null=True, blank=False)
    height = models.PositiveIntegerField(editable=False, null=True, blank=False)
    image = ProcessedImageField(verbose_name=_('image'),
                                storage=hashtag_image_storage,
                                upload_to=upload_to_hashtags_directory,
                                width_field='width',
                                height_field='height',
                                blank=False, null=True, format='JPEG', options={'quality': 60},
                                processors=[ResizeToFit(width=1024, upscale=False)])

    @classmethod
    def create_hashtag(cls, name, color=None, image=None):
        if not color:
            color = generate_random_hex_color()

        name = name.lower()
        tag = cls.objects.create(name=name, color=color, description=None, image=image)

        return tag

    @classmethod
    def get_or_create_hashtag_with_name_and_post(cls, name, post):
        try:
            hashtag = cls.objects.get(name=name)
        except cls.DoesNotExist:
            hashtag = cls.create_hashtag(name=name)

        if not hashtag.has_image() and post.is_public_post():
            post_first_media_image = post.get_first_media_image()
            if post_first_media_image:
                hashtag.image = post_first_media_image.image
                hashtag.save()

        return hashtag

    @classmethod
    def hashtag_with_name_exists(cls, hashtag_name):
        return cls.objects.filter(name=hashtag_name).exists()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Hashtag, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.delete_media()
        super(Hashtag, self).delete(*args, **kwargs)

    def delete_media(self):
        if self.has_image():
            delete_file_field(self.image)

    def has_image(self):
        if hasattr(self, 'image'):

            if self.image:
                return True

        return False
