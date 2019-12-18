from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone

# Create your models here.
from django.utils.translation import ugettext_lazy as _
from imagekit.models import ProcessedImageField
from pilkit.processors import ResizeToFit

from openbook.storage_backends import S3PrivateMediaStorage
from openbook_common.models import Emoji
from openbook_common.utils.helpers import delete_file_field, get_random_pastel_color
from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community
from openbook_hashtags.helpers import upload_to_hashtags_directory
from openbook_hashtags.validators import hashtag_name_validator
from openbook_posts.models import Post, PostComment
from openbook_posts.queries import make_only_public_posts_query

hashtag_image_storage = S3PrivateMediaStorage() if settings.IS_PRODUCTION else default_storage


class Hashtag(models.Model):

    moderated_object = GenericRelation('openbook_moderation.ModeratedObject', related_query_name='hashtags')

    name = models.CharField(_('name'), max_length=settings.HASHTAG_NAME_MAX_LENGTH, blank=False, null=False,
                            validators=[hashtag_name_validator],
                            unique=True)
    color = models.CharField(_('color'), max_length=settings.COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    text_color = models.CharField(_('text color'), max_length=settings.COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                                  validators=[hex_color_validator], default='#ffffff')
    created = models.DateTimeField(editable=False)
    posts = models.ManyToManyField(Post, related_name='hashtags')
    post_comments = models.ManyToManyField(PostComment, related_name='hashtags')
    width = models.PositiveIntegerField(editable=False, null=True, blank=False)
    height = models.PositiveIntegerField(editable=False, null=True, blank=False)
    image = ProcessedImageField(verbose_name=_('image'),
                                storage=hashtag_image_storage,
                                upload_to=upload_to_hashtags_directory,
                                width_field='width',
                                height_field='height',
                                blank=True, null=True, format='JPEG', options={'quality': 60},
                                processors=[ResizeToFit(width=1024, upscale=False)])
    emoji = models.ForeignKey(Emoji, on_delete=models.SET_NULL, related_name='hashtags', null=True, blank=True)

    @classmethod
    def create_hashtag(cls, name, color=None, image=None):
        if not color:
            color = get_random_pastel_color()

        name = name.lower()
        tag = cls.objects.create(name=name, color=color, image=image)

        return tag

    @classmethod
    def get_or_create_hashtag(cls, name, post=None):
        try:
            hashtag = cls.objects.get(name=name)
        except cls.DoesNotExist:
            hashtag = cls.create_hashtag(name=name)

        if post:
            hashtag.attempt_update_media_with_post(post=post)

        return hashtag

    @classmethod
    def hashtag_with_name_exists(cls, hashtag_name):
        return cls.objects.filter(name=hashtag_name).exists()

    def __str__(self):
        return '#%s' % self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()

        self.full_clean()

        return super(Hashtag, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.delete_media()
        super(Hashtag, self).delete(*args, **kwargs)

    def attempt_update_media_with_post(self, post):
        if not self.has_image() and post and post.is_publicly_visible():
            post_first_media_image = post.get_first_media_image()
            if post_first_media_image:
                image_copy = ContentFile(post_first_media_image.content_object.image.read())
                image_copy.name = post_first_media_image.content_object.image.name
                self.image.save(image_copy.name, image_copy)
                self.save()

    def count_posts(self):
        public_posts_query = make_only_public_posts_query()
        return self.posts.filter(public_posts_query).count()

    def delete_media(self):
        if self.has_image():
            delete_file_field(self.image)

    def has_image(self):
        if hasattr(self, 'image'):

            if self.image:
                return True

        return False
