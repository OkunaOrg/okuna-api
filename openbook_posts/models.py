# Create your models here.
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count

# Create your views here.
from rest_framework.exceptions import ValidationError

from django.conf import settings
from openbook.storage_backends import S3PrivateMediaStorage
from openbook_auth.models import User

from openbook_common.models import Emoji
from openbook_common.utils.model_loaders import get_post_reaction_model, get_emoji_model, get_post_comment_model, \
    get_circle_model


class Post(models.Model):
    text = models.CharField(_('text'), max_length=settings.POST_MAX_LENGTH, blank=False, null=True)
    created = models.DateTimeField(editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    public_comments = models.BooleanField(_('public comments'), default=True, editable=False, null=False)
    public_reactions = models.BooleanField(_('public reactions'), default=True, editable=False, null=False)

    @classmethod
    def post_with_id_has_public_comments(cls, post_id):
        return Post.objects.filter(pk=post_id, public_comments=True).count() == 1

    @classmethod
    def post_with_id_has_public_reactions(cls, post_id):
        return Post.objects.filter(pk=post_id, public_reactions=True).count() == 1

    @classmethod
    def create_post(cls, creator, circles_ids, image=None, text=None):
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

    @classmethod
    def get_emoji_counts_for_post_with_id(cls, post_id, emoji_id=None, reactor_id=None):
        PostReaction = get_post_reaction_model()
        Emoji = get_emoji_model()

        emoji_query = Q(reactions__post_id=post_id)

        if emoji_id:
            emoji_query.add(Q(reactions__emoji_id=emoji_id), Q.AND)

        emojis_reacted_with = Emoji.objects.filter(emoji_query).distinct()

        emoji_counts = []

        for emoji in emojis_reacted_with:
            reaction_query = Q(post_id=post_id, emoji_id=emoji.pk)

            if reactor_id:
                reaction_query.add(Q(reactor_id=reactor_id), Q.AND)

            emoji_count = PostReaction.objects.filter(reaction_query).count()
            emoji_counts.append({
                'emoji': emoji,
                'count': emoji_count
            })

        emoji_counts.sort(key=lambda x: x['count'], reverse=True)

        return emoji_counts

    @classmethod
    def get_trending_posts(cls):
        Circle = get_circle_model()
        world_circle_id = Circle.get_world_circle_id()
        return cls.objects.annotate(Count('reactions')).filter(circles__id=world_circle_id).order_by(
            '-reactions__count', '-created')

    def count_comments(self, commenter_id=None):
        return PostComment.count_comments_for_post_with_id(self.pk, commenter_id=commenter_id)

    def count_reactions(self, reactor_id=None):
        return PostReaction.count_reactions_for_post_with_id(self.pk, reactor_id=reactor_id)

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
        Circle = get_circle_model()
        world_circle_id = Circle.get_world_circle_id()
        if self.circles.filter(id=world_circle_id).count() == 1:
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

    @classmethod
    def count_comments_for_post_with_id(cls, post_id, commenter_id=None):
        count_query = Q(post_id=post_id)

        if commenter_id:
            count_query.add(Q(commenter_id=commenter_id), Q.AND)

        return cls.objects.filter(count_query).count()

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

    @classmethod
    def count_reactions_for_post_with_id(cls, post_id, reactor_id=None):
        count_query = Q(post_id=post_id)

        if reactor_id:
            count_query.add(Q(reactor_id=reactor_id), Q.AND)

        return cls.objects.filter(count_query).count()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostReaction, self).save(*args, **kwargs)
