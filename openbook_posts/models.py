# Create your models here.
import uuid
from datetime import timedelta

from django.contrib.contenttypes.fields import GenericRelation
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count

# Create your views here.
from pilkit.processors import ResizeToFit
from rest_framework.exceptions import ValidationError

from django.conf import settings
from openbook.storage_backends import S3PrivateMediaStorage
from openbook_auth.models import User

from openbook_common.models import Emoji
from openbook_common.utils.model_loaders import get_emoji_model, \
    get_circle_model, get_community_model
from imagekit.models import ProcessedImageField

from openbook_posts.helpers import upload_to_post_image_directory, upload_to_post_video_directory


class Post(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    text = models.CharField(_('text'), max_length=settings.POST_MAX_LENGTH, blank=False, null=True)
    created = models.DateTimeField(editable=False, db_index=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    comments_enabled = models.BooleanField(_('comments enabled'), default=True, editable=False, null=False)
    public_reactions = models.BooleanField(_('public reactions'), default=True, editable=False, null=False)
    community = models.ForeignKey('openbook_communities.Community', on_delete=models.CASCADE, related_name='posts',
                                  null=True,
                                  blank=False)
    is_edited = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    moderation_object = GenericRelation('openbook_moderation.ModeratedObject', related_query_name='posts')

    class Meta:
        index_together = [
            ('creator', 'community'),
        ]

    @classmethod
    def get_post_id_for_post_with_uuid(cls, post_uuid):
        post = cls.objects.values('id').get(uuid=post_uuid)
        return post['id']

    @classmethod
    def post_with_id_has_public_reactions(cls, post_id):
        return Post.objects.filter(pk=post_id, public_reactions=True).exists()

    @classmethod
    def is_post_with_id_a_community_post(cls, post_id):
        return Post.objects.filter(pk=post_id, community__isnull=False).exists()

    @classmethod
    def create_post(cls, creator, circles_ids=None, community_name=None, image=None, text=None, video=None,
                    created=None):

        if not community_name and not circles_ids:
            raise ValidationError(_('A post requires circles or a community to be posted to.'))

        if community_name and circles_ids:
            raise ValidationError(_('A post cannot be posted both to a community and to circles.'))

        if not text and not image and not video:
            raise ValidationError(_('A post requires text or an image/video.'))

        if image and video:
            raise ValidationError(_('A post must have an image or a video, not both.'))

        post = Post.objects.create(creator=creator, created=created)

        if text:
            post.text = text

        if image:
            PostImage.objects.create(image=image, post_id=post.pk)

        if video:
            PostVideo.objects.create(video=video, post_id=post.pk)

        if circles_ids:
            post.circles.add(*circles_ids)
        else:
            Community = get_community_model()
            post.community = Community.objects.get(name=community_name)

        post.save()

        return post

    @classmethod
    def get_public_emoji_counts_for_post_with_id(cls, post_id, emoji_id=None, reactor_id=None):
        Emoji = get_emoji_model()

        emoji_query = Q(reactions__post_id=post_id, )

        if emoji_id:
            emoji_query.add(Q(reactions__emoji_id=emoji_id), Q.AND)

        if reactor_id:
            emoji_query.add(Q(reactions__reactor_id=reactor_id), Q.AND)

        emojis = Emoji.objects.filter(emoji_query).annotate(Count('reactions')).distinct().order_by(
            '-reactions__count').cache().all()

        return [{'emoji': emoji, 'count': emoji.reactions__count} for emoji in emojis]

    @classmethod
    def get_trending_posts_for_user_with_id(cls, user_id):
        trending_posts_query = cls._get_trending_posts_query()
        trending_posts_query.add(~Q(community__banned_users__id=user_id), Q.AND)
        trending_posts_query.add(Q(is_closed=False), Q.AND)

        trending_posts_query.add(~Q(Q(creator__blocked_by_users__blocker_id=user_id) | Q(
            creator__user_blocks__blocked_user_id=user_id)), Q.AND)
        return cls._get_trending_posts_with_query(query=trending_posts_query)

    @classmethod
    def _get_trending_posts_with_query(cls, query):
        return cls.objects.annotate(Count('reactions')).filter(query).order_by(
            '-reactions__count', '-created')

    @classmethod
    def _get_trending_posts_query(cls):
        trending_posts_query = Q(created__gte=timezone.now() - timedelta(
            hours=12))

        Community = get_community_model()

        trending_posts_sources_query = Q(community__type=Community.COMMUNITY_TYPE_PUBLIC)

        trending_posts_query.add(trending_posts_sources_query, Q.AND)

        return trending_posts_query

    @classmethod
    def get_post_comment_notification_target_users(cls, post_id, post_commenter_id):
        """
        Returns the users that should be notified of a post comment.
        This includes the post creator and other post commenters
        :param post_id:
        :param post_commenter_id:
        :return:
        """
        post_notification_target_users_query = Q(posts_comments__post_id=post_id)
        post_notification_target_users_query.add(Q(posts__id=post_id), Q.OR)
        post_notification_target_users_query.add(~Q(id=post_commenter_id), Q.AND)

        return User.objects.filter(post_notification_target_users_query).distinct()

    def count_comments(self):
        return PostComment.count_comments_for_post_with_id(self.pk)

    def count_reactions(self, reactor_id=None):
        return PostReaction.count_reactions_for_post_with_id(self.pk, reactor_id=reactor_id)

    def is_text_only_post(self):
        return self.has_text() and not self.has_video() and not self.has_image()

    def has_text(self):
        if hasattr(self, 'text'):

            if self.text:
                return True

        return False

    def has_image(self):
        if hasattr(self, 'image'):

            if self.image:
                return True

        return False

    def has_video(self):
        if hasattr(self, 'video'):

            if self.video:
                return True

        return False

    def comment(self, text, commenter):
        return PostComment.create_comment(text=text, commenter=commenter, post=self)

    def react(self, reactor, emoji_id):
        return PostReaction.create_reaction(reactor=reactor, emoji_id=emoji_id, post=self)

    def is_public_post(self):
        Circle = get_circle_model()
        world_circle_id = Circle.get_world_circle_id()
        if self.circles.filter(id=world_circle_id).exists():
            return True
        return False

    def is_encircled_post(self):
        return not self.is_public_post() and not self.community

    def update(self, text=None):
        self._check_can_be_updated(text=text)
        self.text = text
        self.is_edited = True
        self.save()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id and not self.created:
            self.created = timezone.now()

        return super(Post, self).save(*args, **kwargs)

    def _check_can_be_updated(self, text=None):
        if self.is_text_only_post() and not text:
            raise ValidationError(
                _('Cannot remove the text of a text only post. Try deleting it instead.')
            )


post_image_storage = S3PrivateMediaStorage() if settings.IS_PRODUCTION else default_storage


class PostImage(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='image')
    image = ProcessedImageField(verbose_name=_('image'), storage=post_image_storage,
                                upload_to=upload_to_post_image_directory,
                                width_field='width',
                                height_field='height',
                                blank=False, null=True, format='JPEG', options={'quality': 50},
                                processors=[ResizeToFit(width=1024, upscale=False)])
    width = models.PositiveIntegerField(editable=False, null=False, blank=False)
    height = models.PositiveIntegerField(editable=False, null=False, blank=False)


class PostVideo(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='video')
    video = models.FileField(_('video'), blank=False, null=False, storage=post_image_storage,
                             upload_to=upload_to_post_video_directory)


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    created = models.DateTimeField(editable=False, db_index=True)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts_comments')
    text = models.CharField(_('text'), max_length=settings.POST_COMMENT_MAX_LENGTH, blank=False, null=False)
    is_edited = models.BooleanField(default=False, null=False, blank=False)
    moderation_object = GenericRelation('openbook_moderation.ModeratedObject', related_query_name='post_comments')

    @classmethod
    def create_comment(cls, text, commenter, post):
        return PostComment.objects.create(text=text, commenter=commenter, post=post)

    @classmethod
    def count_comments_for_post_with_id(cls, post_id):
        count_query = Q(post_id=post_id)

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


class PostMute(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='mutes')
    muter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_mutes')

    class Meta:
        unique_together = ('post', 'muter',)

    @classmethod
    def create_post_mute(cls, post_id, muter_id):
        return cls.objects.create(post_id=post_id, muter_id=muter_id)
