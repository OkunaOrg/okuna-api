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

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def reactions_count(self):
        return self.reactions.count()

    def has_text(self):
        if self.text:
            return True
        return False

    def has_image(self):
        if self.image:
            return True
        return False

    def comment(self, text, commenter):
        return PostComment.create_comment(text=text, commenter=commenter, post=self)

    def remove_comment_with_id(self, post_comment_id):
        self.comments.filter(id=post_comment_id).delete()

    def react(self, reactor, emoji_id):
        return PostReaction.create_reaction(reactor=reactor, emoji_id=emoji_id, post=self)

    def remove_reaction_with_id(self, reaction_id):
        self.reactions.filter(id=reaction_id).delete()

    def is_public_post(self):
        creator = self.creator
        creator_world_circle_id = creator.world_circle_id
        if self.circles.filter(id=creator_world_circle_id).count() == 1:
            return True
        return False

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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    created = models.DateTimeField(editable=False)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts_comments')
    text = models.CharField(_('text'), max_length=settings.POST_COMMENT_MAX_LENGTH, blank=False, null=False)

    @classmethod
    def create_comment(cls, text, commenter, post):
        return PostComment.objects.create(text=text, commenter=commenter, post=post)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostComment, self).save(*args, **kwargs)


class PostReaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    created = models.DateTimeField(editable=False)
    reactor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reactions')
    emoji = models.ForeignKey(Emoji, on_delete=models.CASCADE, related_name='reactions')

    class Meta:
        unique_together = ('reactor', 'post',)

    @classmethod
    def create_reaction(cls, reactor, emoji_id, post):
        return PostReaction.objects.create(reactor=reactor, emoji_id=emoji_id, post=post)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostReaction, self).save(*args, **kwargs)
