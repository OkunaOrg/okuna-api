# Create your models here.
import os
import tempfile
import uuid
from datetime import timedelta

from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile, SimpleUploadedFile
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count
import ffmpy

# Create your views here.
from ordered_model.models import OrderedModel
from pilkit.processors import ResizeToFit
from rest_framework.exceptions import ValidationError

from django.conf import settings

from openbook_common.peekalink_client import peekalink_client
from openbook_posts.validators import post_text_validators, post_comment_text_validators
from video_encoding.backends import get_backend
from video_encoding.fields import VideoField
from video_encoding.models import Format

from openbook.storage_backends import S3PrivateMediaStorage
from openbook_auth.models import User

from openbook_common.models import Emoji, Language
from openbook_common.utils.helpers import delete_file_field, sha256sum, extract_usernames_from_string, get_magic, \
    write_in_memory_file_to_disk, extract_hashtags_from_string, normalize_url
from openbook_common.utils.model_loaders import get_emoji_model, \
    get_circle_model, get_community_model, get_post_comment_notification_model, \
    get_post_comment_reply_notification_model, get_post_reaction_notification_model, get_moderated_object_model, \
    get_post_user_mention_notification_model, get_post_comment_user_mention_notification_model, get_user_model, \
    get_post_user_mention_model, get_post_comment_user_mention_model, get_community_notifications_subscription_model, \
    get_community_new_post_notification_model, get_user_new_post_notification_model, \
    get_hashtag_model, get_user_notifications_subscription_model, get_trending_post_model, \
    get_post_comment_reaction_notification_model
from imagekit.models import ProcessedImageField

from openbook_moderation.models import ModeratedObject
from openbook_notifications.helpers import send_post_comment_user_mention_push_notification, \
    send_post_user_mention_push_notification, send_community_new_post_push_notification, \
    send_user_new_post_push_notification
from openbook_posts.checkers import check_can_be_updated, check_can_add_media, check_can_be_published, \
    check_mimetype_is_supported_media_mimetypes
from openbook_posts.helpers import upload_to_post_image_directory, upload_to_post_video_directory, \
    upload_to_post_directory
from openbook_posts.jobs import process_post_media

magic = get_magic()
from openbook_common.helpers import get_language_for_text, extract_urls_from_string

post_image_storage = S3PrivateMediaStorage() if settings.IS_PRODUCTION else default_storage


class Post(models.Model):
    moderated_object = GenericRelation(ModeratedObject, related_query_name='posts')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    text = models.TextField(_('text'), max_length=settings.POST_MAX_LENGTH, blank=False, null=True,
                            validators=post_text_validators)
    created = models.DateTimeField(editable=False, db_index=True)
    modified = models.DateTimeField(db_index=True, default=timezone.now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    comments_enabled = models.BooleanField(_('comments enabled'), default=True, editable=False, null=False)
    public_reactions = models.BooleanField(_('public reactions'), default=True, editable=False, null=False)
    community = models.ForeignKey('openbook_communities.Community', on_delete=models.CASCADE, related_name='posts',
                                  null=True,
                                  blank=False)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, related_name='posts')
    is_edited = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    STATUS_DRAFT = 'D'
    STATUS_PROCESSING = 'PG'
    STATUS_PUBLISHED = 'P'
    STATUSES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_PUBLISHED, 'Published'),
    )
    status = models.CharField(blank=False, null=False, choices=STATUSES, default=STATUS_DRAFT, max_length=2)
    media_height = models.PositiveSmallIntegerField(_('media height'), null=True)
    media_width = models.PositiveSmallIntegerField(_('media width'), null=True)
    media_thumbnail = ProcessedImageField(verbose_name=_('thumbnail'), storage=post_image_storage,
                                          upload_to=upload_to_post_directory,
                                          blank=False, null=True, format='JPEG', options={'quality': 30},
                                          processors=[ResizeToFit(width=512, upscale=False)])

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
                    created=None, is_draft=False):

        if not community_name and not circles_ids:
            raise ValidationError(_('A post requires circles or a community to be posted to.'))

        if community_name and circles_ids:
            raise ValidationError(_('A post cannot be posted both to a community and to circles.'))

        post = Post.objects.create(creator=creator, created=created)

        if image and video:
            raise ValidationError(_('A post must have an image or a video, not both.'))

        if text:
            post.text = text
            post.language = get_language_for_text(text)

        if image:
            post.add_media(file=image)
        elif video:
            post.add_media(file=video)

        if circles_ids:
            post.circles.add(*circles_ids)
        else:
            Community = get_community_model()
            post.community = Community.objects.get(name=community_name)

        # If on create we have a video or image, we automatically publish it
        # Backwards compat reasons.
        if not is_draft:
            post.publish()
        else:
            post.save()

        return post

    @classmethod
    def get_emoji_counts_for_post_with_id(cls, post_id, emoji_id=None, reactor_id=None):
        Emoji = get_emoji_model()
        return Emoji.get_emoji_counts_for_post_with_id(post_id=post_id, emoji_id=emoji_id, reactor_id=reactor_id)

    @classmethod
    def get_trending_posts_for_user_with_id(cls, user_id, max_id=None, min_id=None):
        """
        Gets trending posts (communities only) for authenticated user excluding reported, closed, blocked users posts
        """
        Post = cls
        TrendingPost = get_trending_post_model()
        Community = get_community_model()

        posts_select_related = ('post__creator', 'post__creator__profile', 'post__community', 'post__image')
        posts_prefetch_related = ('post__circles', 'post__creator__profile__badges', 'post__reactions__reactor')

        posts_only = ('id',
                      'post__text', 'post__id', 'post__uuid', 'post__created', 'post__image__width',
                      'post__image__height', 'post__image__image',
                      'post__creator__username', 'post__creator__id', 'post__creator__profile__name',
                      'post__creator__profile__avatar',
                      'post__creator__profile__badges__id', 'post__creator__profile__badges__keyword',
                      'post__creator__profile__id', 'post__community__id', 'post__community__name',
                      'post__community__avatar',
                      'post__community__color', 'post__community__title')

        reported_posts_exclusion_query = ~Q(post__moderated_object__reports__reporter_id=user_id)

        trending_community_posts_query = Q(post__is_closed=False,
                                           post__is_deleted=False,
                                           post__status=Post.STATUS_PUBLISHED)

        trending_community_posts_query.add(~Q(Q(post__creator__blocked_by_users__blocker_id=user_id) | Q(
            post__creator__user_blocks__blocked_user_id=user_id)), Q.AND)
        trending_community_posts_query.add(Q(post__community__type=Community.COMMUNITY_TYPE_PUBLIC), Q.AND)
        trending_community_posts_query.add(~Q(post__community__banned_users__id=user_id), Q.AND)

        if max_id:
            trending_community_posts_query.add(Q(id__lt=max_id), Q.AND)
        elif min_id:
            trending_community_posts_query.add(Q(id__gt=min_id), Q.AND)

        ModeratedObject = get_moderated_object_model()
        trending_community_posts_query.add(~Q(post__moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

        trending_community_posts_query.add(reported_posts_exclusion_query, Q.AND)

        trending_community_posts_queryset = TrendingPost.objects. \
            select_related(*posts_select_related). \
            prefetch_related(*posts_prefetch_related). \
            only(*posts_only). \
            filter(trending_community_posts_query)

        return trending_community_posts_queryset

    @classmethod
    def get_trending_posts_old_for_user_with_id(cls, user_id):
        """
        For backwards compatibility reasons
        """
        trending_posts_query = cls._get_trending_posts_old_query()
        trending_posts_query.add(~Q(community__banned_users__id=user_id), Q.AND)

        trending_posts_query.add(~Q(Q(creator__blocked_by_users__blocker_id=user_id) | Q(
            creator__user_blocks__blocked_user_id=user_id)), Q.AND)

        trending_posts_query.add(~Q(moderated_object__reports__reporter_id=user_id), Q.AND)

        trending_posts_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

        return cls._get_trending_posts_old_with_query(query=trending_posts_query)

    @classmethod
    def _get_trending_posts_old_with_query(cls, query):
        return cls.objects.filter(query).annotate(Count('reactions')).order_by(
            '-reactions__count', '-created')

    @classmethod
    def _get_trending_posts_old_query(cls):
        trending_posts_query = Q(created__gte=timezone.now() - timedelta(
            hours=12))

        Community = get_community_model()

        trending_posts_sources_query = Q(community__type=Community.COMMUNITY_TYPE_PUBLIC, status=cls.STATUS_PUBLISHED,
                                         is_closed=False, is_deleted=False)

        trending_posts_query.add(trending_posts_sources_query, Q.AND)

        return trending_posts_query

    @classmethod
    def get_post_comment_notification_target_users(cls, post, post_commenter):
        """
        Returns the users that should be notified of a post comment.
        This includes the post creator and other post commenters
        :return:
        """

        # Add other post commenters, exclude replies to comments, the post commenter
        other_commenters = User.objects.filter(
            Q(posts_comments__post_id=post.pk, posts_comments__parent_comment_id=None, ) & ~Q(
                id=post_commenter.pk))

        post_creator = User.objects.filter(pk=post.creator_id)

        return other_commenters.union(post_creator)

    @classmethod
    def get_post_comment_reply_notification_target_users(cls, post_commenter, parent_post_comment):
        """
        Returns the users that should be notified of a post comment reply.
        :return:
        """

        # Add other post commenters, exclude non replies, the post commenter
        other_repliers = User.objects.filter(
            Q(posts_comments__parent_comment_id=parent_post_comment.pk, ) & ~Q(
                id=post_commenter.pk))

        # Add post comment creator
        post_comment_creator = User.objects.filter(pk=parent_post_comment.commenter_id)

        # Add post creator
        post = parent_post_comment.post
        post_creator = User.objects.filter(pk=post.creator.id)
        return other_repliers.union(post_comment_creator, post_creator)

    @classmethod
    def get_community_notification_target_subscriptions(cls, post):
        CommunityNotificationsSubscription = get_community_notifications_subscription_model()

        community_subscriptions_query = Q(community=post.community, new_post_notifications=True)

        exclude_blocked_users_query = Q(Q(subscriber__blocked_by_users__blocker_id=post.creator.pk) | Q(
            subscriber__user_blocks__blocked_user_id=post.creator.pk))
        community_members_query = Q(subscriber__communities_memberships__community_id=post.community.pk)
        exclude_self_query = ~Q(subscriber=post.creator)

        # Exclude banned users
        exclude_blocked_users_query.add(Q(subscriber__banned_of_communities__id=post.community.pk), Q.OR)

        # Subscriptions after excluding blocked users
        target_subscriptions_excluding_blocked = CommunityNotificationsSubscription.objects. \
            filter(community_subscriptions_query &
                   community_members_query &
                   exclude_self_query
                   ). \
            exclude(exclude_blocked_users_query)

        staff_members_query = Q(subscriber__communities_memberships__community_id=post.community.pk,
                                subscriber__communities_memberships__is_administrator=True) | \
                              Q(subscriber__communities_memberships__community_id=post.community.pk,
                                subscriber__communities_memberships__is_moderator=True)

        # Subscriptions from staff of community
        target_subscriptions_with_staff = CommunityNotificationsSubscription.objects. \
            filter(community_subscriptions_query &
                   community_members_query &
                   staff_members_query &
                   exclude_self_query
                   )

        results = target_subscriptions_excluding_blocked.union(target_subscriptions_with_staff)

        return results

    @classmethod
    def get_user_notification_target_subscriptions(cls, post):
        UserNotificationsSubscription = get_user_notifications_subscription_model()

        user_subscriptions_query = Q(user=post.creator, new_post_notifications=True)

        exclude_blocked_users_query = Q(Q(subscriber__blocked_by_users__blocker_id=post.creator.pk) | Q(
            subscriber__user_blocks__blocked_user_id=post.creator.pk))
        exclude_self_query = ~Q(subscriber=post.creator)

        if post.is_encircled_post():
            circle_ids = [circle.pk for circle in post.circles.all()]
            post_circles_query = Q(subscriber__connections__target_connection__circles__in=circle_ids)
            user_subscriptions_query.add(post_circles_query, Q.AND)

        user_subscriptions_query.add(exclude_self_query, Q.AND)

        # Subscriptions after excluding blocked users
        target_subscriptions = UserNotificationsSubscription.objects. \
            filter(user_subscriptions_query). \
            exclude(exclude_blocked_users_query)

        return target_subscriptions

    def count_comments(self):
        return PostComment.count_comments_for_post_with_id(self.pk)

    def count_comments_with_user(self, user):
        # Count comments excluding users blocked by authenticated user
        count_query = ~Q(Q(commenter__blocked_by_users__blocker_id=user.pk) | Q(
            commenter__user_blocks__blocked_user_id=user.pk))

        if self.community:
            if not user.is_staff_of_community_with_name(community_name=self.community.name):
                # Dont retrieve comments except from staff members
                blocked_users_query_staff_members = Q(
                    commenter__communities_memberships__community_id=self.community.pk)
                blocked_users_query_staff_members.add(Q(commenter__communities_memberships__is_administrator=True) | Q(
                    commenter__communities_memberships__is_moderator=True), Q.AND)

                count_query.add(~blocked_users_query_staff_members, Q.AND)

            # Don't count items that have been reported and approved by community moderators
            ModeratedObject = get_moderated_object_model()
            count_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

        # Dont count soft deleted items
        count_query.add(Q(is_deleted=False), Q.AND)

        # Dont count items we have reported
        count_query.add(~Q(moderated_object__reports__reporter_id=user.pk), Q.AND)

        return self.comments.filter(count_query).count()

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

    def has_links(self):
        return self.links.exists()

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

    def is_public_community_post(self):
        Community = get_community_model()
        return Community.objects.filter(posts__id=self.pk, type=Community.COMMUNITY_TYPE_PUBLIC).exists()

    def is_publicly_visible(self):
        return self.is_public_post() or self.is_public_community_post()

    def is_encircled_post(self):
        return not self.is_public_post() and not self.community

    def update(self, text=None):
        check_can_be_updated(post=self, text=text)
        self.text = text
        self.is_edited = True
        self.language = get_language_for_text(text)
        self.save()

    def get_media(self):
        return self.media

    def add_media(self, file, order=None):
        check_can_add_media(post=self)

        is_in_memory_file = isinstance(file, InMemoryUploadedFile) or isinstance(file, SimpleUploadedFile)

        if is_in_memory_file:
            file_mime = magic.from_buffer(file.read())
        elif isinstance(file, TemporaryUploadedFile):
            file_mime = magic.from_file(file.temporary_file_path())
        else:
            file_mime = magic.from_file(file.name)

        check_mimetype_is_supported_media_mimetypes(file_mime)
        # Mime check moved pointer
        file.seek(0)

        file_mime_types = file_mime.split('/')

        file_mime_type = file_mime_types[0]
        file_mime_subtype = file_mime_types[1]

        temp_files_to_close = []

        if file_mime_subtype == 'gif':
            if is_in_memory_file:
                file = write_in_memory_file_to_disk(file)

            temp_dir = tempfile.gettempdir()
            converted_gif_file_name = os.path.join(temp_dir, str(uuid.uuid4()) + '.mp4')

            ff = ffmpy.FFmpeg(
                inputs={file.temporary_file_path() if hasattr(file, 'temporary_file_path') else file.name: None},
                outputs={converted_gif_file_name: None})
            ff.run()
            converted_gif_file = open(converted_gif_file_name, 'rb')
            temp_files_to_close.append(converted_gif_file)
            file = File(file=converted_gif_file)
            file_mime_type = 'video'

        has_other_media = self.media.exists()

        if file_mime_type == 'image':
            post_image = self._add_media_image(image=file, order=order)
            if not has_other_media:
                self.media_width = post_image.width
                self.media_height = post_image.height
                self.media_thumbnail = file
        elif file_mime_type == 'video':
            post_video = self._add_media_video(video=file, order=order)
            if not has_other_media:
                self.media_width = post_video.width
                self.media_height = post_video.height
                self.media_thumbnail = post_video.thumbnail.file
        else:
            raise ValidationError(
                _('Unsupported media file type')
            )

        for file_to_close in temp_files_to_close:
            file_to_close.close()

        self.save()

    def get_first_media(self):
        return self.media.first()

    def get_first_media_image(self):
        return self.media.filter(type=PostMedia.MEDIA_TYPE_IMAGE).first()

    def _add_media_image(self, image, order):
        return PostImage.create_post_media_image(image=image, post_id=self.pk, order=order)

    def _add_media_video(self, video, order):
        return PostVideo.create_post_media_video(file=video, post_id=self.pk, order=order)

    def count_media(self):
        return self.media.count()

    def publish(self):
        check_can_be_published(post=self)

        if self.has_media():
            # After finishing, this will call _publish()
            self.status = Post.STATUS_PROCESSING
            self.save()
            process_post_media.delay(post_id=self.pk)
        else:
            self._publish()

    def _publish(self):
        self.status = Post.STATUS_PUBLISHED
        self.created = timezone.now()
        self._process_post_subscribers()
        self.save()

    def is_draft(self):
        return self.status == Post.STATUS_DRAFT

    def is_empty(self):
        return not self.text and not hasattr(self, 'image') and not hasattr(self, 'video') and not self.has_media()

    def has_media(self):
        return self.media.exists()

    def save(self, *args, **kwargs):
        ''' On create, update timestamps '''
        if not self.id and not self.created:
            self.created = timezone.now()

        self.modified = timezone.now()

        post = super(Post, self).save(*args, **kwargs)

        self._process_post_mentions()
        self._process_post_hashtags()
        self._process_post_links()

        return post

    def delete(self, *args, **kwargs):
        self.delete_media()
        super(Post, self).delete(*args, **kwargs)

    def delete_media(self):
        if self.has_image():
            delete_file_field(self.image.image)

    def soft_delete(self):
        self.delete_notifications()
        for comment in self.comments.all().iterator():
            comment.soft_delete()
        self.is_deleted = True
        self.save()

    def unsoft_delete(self):
        self.is_deleted = False
        for comment in self.comments.all().iterator():
            comment.unsoft_delete()
        self.save()

    def delete_notifications(self):
        # Remove all post reaction notifications
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.objects.filter(post_reaction__post_id=self.pk).delete()

        # Remove all post user mention notifications
        PostUserMentionNotification = get_post_user_mention_notification_model()
        PostUserMentionNotification.objects.filter(post_user_mention__post_id=self.pk).delete()

        # Remove all post comment notifications
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.objects.filter(post_comment__post_id=self.pk).delete()

        # Remove all post comment reply notifications
        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        PostCommentReplyNotification.objects.filter(post_comment__post_id=self.pk).delete()

        # Remove all post comment reaction notifications
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.objects.filter(
            post_comment_reaction__post_comment__post_id=self.pk).delete()

        # Remove all post comment user mention notifications
        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        PostCommentUserMentionNotification.objects.filter(
            post_comment_user_mention__post_comment__post_id=self.pk).delete()

        # Remove all community new post notifications
        CommunityNewPostNotification = get_community_new_post_notification_model()
        CommunityNewPostNotification.objects.filter(post_id=self.pk).delete()

        # Remove all user new post notifications
        UserNewPostNotification = get_user_new_post_notification_model()
        UserNewPostNotification.objects.filter(post_id=self.pk).delete()

    def delete_notifications_for_user(self, user):
        # Remove all post reaction notifications
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.objects.filter(
            notification__owner_id=user.pk,
            post_reaction__post_id=self.pk).delete()

        # Remove all post user mention notifications
        PostUserMentionNotification = get_post_user_mention_notification_model()
        PostUserMentionNotification.objects.filter(
            notification__owner_id=user.pk,
            post_user_mention__post_id=self.pk).delete()

        # Remove all post comment notifications
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.objects.filter(post_comment__post_id=self.pk,
                                               notification__owner_id=user.pk).delete()

        # Remove all post comment reply notifications
        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        PostCommentReplyNotification.objects.filter(post_comment__post_id=self.pk,
                                                    notification__owner_id=user.pk).delete()

        # Remove all post comment user mention notifications
        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        PostCommentUserMentionNotification.objects.filter(
            notification__owner_id=user.pk,
            post_comment_user_mention__post_comment__post_id=self.pk).delete()

        # Remove all post comment reaction notifications
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.objects.filter(
            notification__owner_id=user.pk,
            post_comment_reaction__post_comment__post_id=self.pk).delete()

        # Remove all community new post notifications
        CommunityNewPostNotification = get_community_new_post_notification_model()
        CommunityNewPostNotification.objects.filter(notification__owner_id=user.pk,
                                                    post_id=self.pk).delete()

        # Remove all user new post notifications
        UserNewPostNotification = get_user_new_post_notification_model()
        UserNewPostNotification.objects.filter(notification__owner_id=user.pk,
                                               post_id=self.pk).delete()

    def delete_notifications_except_for_users(self, excluded_users):
        excluded_ids = [user.pk for user in excluded_users]

        # Remove all post user mention notifications
        PostUserMentionNotification = get_post_user_mention_notification_model()
        PostUserMentionNotification.objects.filter(post_user_mention__post_id=self.pk).exclude(
            notification__owner_id__in=excluded_ids).delete()

        # Remove all post comment notifications
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.objects.filter(post_comment__post_id=self.pk). \
            exclude(notification__owner_id__in=excluded_ids).delete()

        # Remove all post reaction notifications
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.objects.filter(post_reaction__post_id=self.pk).exclude(
            notification__owner_id__in=excluded_ids).delete()

        # Remove all post comment reply notifications
        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        PostCommentReplyNotification.objects.filter(post_comment__post_id=self.pk).exclude(
            notification__owner_id__in=excluded_ids).delete()

        # Remove all post comment reaction notifications
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.objects.filter(post_comment_reaction__post_comment__post_id=self.pk).exclude(
            notification__owner_id__in=excluded_ids).delete()

        # Remove all post comment user mention notifications
        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        PostCommentUserMentionNotification.objects.filter(
            post_comment_user_mention__post_comment__post_id=self.pk).exclude(
            notification__owner_id__in=excluded_ids).delete()

        # Remove all community new post notifications
        CommunityNewPostNotification = get_community_new_post_notification_model()
        CommunityNewPostNotification.objects.filter(post_id=self.pk).exclude(
            notification__owner_id__in=excluded_ids).delete()

        # Remove all user new post notifications
        UserNewPostNotification = get_user_new_post_notification_model()
        UserNewPostNotification.objects.filter(post_id=self.pk).exclude(
            notification__owner_id__in=excluded_ids).delete()

    def get_participants(self):
        User = get_user_model()

        # Add post creator
        post_creator = User.objects.filter(pk=self.creator_id)

        # Add post commentators
        post_commenters = User.objects.filter(posts_comments__post_id=self.pk, is_deleted=False)

        # If community post, add community members
        if self.community:
            community_members = User.objects.filter(communities_memberships__community_id=self.community_id,
                                                    is_deleted=False)
            result = post_creator.union(post_commenters, community_members)
        else:
            result = post_creator.union(post_commenters)

        return result

    def _process_post_mentions(self):
        if not self.text:
            self.user_mentions.all().delete()
        else:
            usernames = extract_usernames_from_string(string=self.text)
            if not usernames:
                self.user_mentions.all().delete()
            else:
                existing_mention_usernames = []
                for existing_mention in self.user_mentions.only('id', 'user__username').all().iterator():
                    existing_mention_username = existing_mention.user.username.lower()
                    if existing_mention_username not in usernames:
                        existing_mention.delete()
                    else:
                        existing_mention_usernames.append(existing_mention_username)

                PostUserMention = get_post_user_mention_model()
                User = get_user_model()

                for username in usernames:
                    username = username.lower()
                    if username not in existing_mention_usernames:
                        try:
                            user = User.objects.only('id', 'username').get(username__iexact=username)
                            user_is_post_creator = user.pk == self.creator_id
                            if user.can_see_post(post=self) and not user_is_post_creator:
                                PostUserMention.create_post_user_mention(user=user, post=self)
                                existing_mention_usernames.append(username)
                        except User.DoesNotExist:
                            pass

    def _process_post_hashtags(self):
        if not self.text:
            self.hashtags.all().delete()
        else:
            hashtags = extract_hashtags_from_string(string=self.text)
            if not hashtags:
                self.hashtags.all().delete()
            else:
                existing_hashtags = []
                for existing_hashtag in self.hashtags.only('id', 'name').all().iterator():
                    if existing_hashtag.name not in hashtags:
                        self.hashtags.remove(existing_hashtag)
                    else:
                        existing_hashtags.append(existing_hashtag.name)

                Hashtag = get_hashtag_model()

                for hashtag in hashtags:
                    hashtag = hashtag.lower()
                    hashtag_obj = Hashtag.get_or_create_hashtag(name=hashtag, post=self)
                    if hashtag not in existing_hashtags:
                        self.hashtags.add(hashtag_obj)

    def _process_post_subscribers(self):
        if self.community:
            CommunityNewPostNotification = get_community_new_post_notification_model()
            community_subscriptions = Post.get_community_notification_target_subscriptions(post=self)

            for subscription in community_subscriptions:
                CommunityNewPostNotification.create_community_new_post_notification(
                    post_id=self.pk,
                    owner_id=subscription.subscriber.pk, community_notifications_subscription_id=subscription.pk)
                send_community_new_post_push_notification(community_notifications_subscription=subscription)
        else:
            UserNewPostNotification = get_user_new_post_notification_model()
            user_subscriptions = Post.get_user_notification_target_subscriptions(post=self)

            for subscription in user_subscriptions:
                UserNewPostNotification.create_user_new_post_notification(
                    post_id=self.pk, owner_id=subscription.subscriber.pk,
                    user_notifications_subscription_id=subscription.pk)
                send_user_new_post_push_notification(user_notifications_subscription=subscription, post=self)

    def _process_post_links(self):
        if self.has_text():
            if not self.has_media():
                link_urls = extract_urls_from_string(self.text)
                if link_urls:
                    self.links.all().delete()
                    for link_url in link_urls:
                        link_url = normalize_url(link_url)
                        post_link = PostLink.create_link(link=link_url, post_id=self.pk)
                        post_link.refresh_has_preview()
            else:
                self.links.all().delete()
        else:
            self.links.all().delete()


class TopPost(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='top_post')
    created = models.DateTimeField(editable=False, db_index=True)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()

        return super(TopPost, self).save(*args, **kwargs)


class TrendingPost(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='trending_post')
    created = models.DateTimeField(editable=False, db_index=True)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()

        return super(TrendingPost, self).save(*args, **kwargs)


class TopPostCommunityExclusion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='top_posts_community_exclusions')
    community = models.ForeignKey('openbook_communities.Community', on_delete=models.CASCADE,
                                  related_name='top_posts_community_exclusions')
    created = models.DateTimeField(editable=False, db_index=True)

    class Meta:
        unique_together = ('user', 'community',)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()

        return super(TopPostCommunityExclusion, self).save(*args, **kwargs)


class ProfilePostsCommunityExclusion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_posts_community_exclusions')
    community = models.ForeignKey('openbook_communities.Community', on_delete=models.CASCADE,
                                  related_name='profile_posts_community_exclusions')
    created = models.DateTimeField(editable=False, db_index=True)

    class Meta:
        unique_together = ('user', 'community',)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()

        return super(ProfilePostsCommunityExclusion, self).save(*args, **kwargs)


class PostMedia(OrderedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    order_with_respect_to = 'post'

    MEDIA_TYPE_VIDEO = 'V'
    MEDIA_TYPE_IMAGE = 'I'

    MEDIA_TYPES = (
        (MEDIA_TYPE_VIDEO, 'Video'),
        (MEDIA_TYPE_IMAGE, 'Image'),
    )

    type = models.CharField(max_length=5, choices=MEDIA_TYPES)

    # Generic relation types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    @classmethod
    def create_post_media(cls, post_id, type, content_object, order):
        return cls.objects.create(type=type, content_object=content_object, post_id=post_id, order=order)


class PostImage(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='image', null=True)
    image = ProcessedImageField(verbose_name=_('image'), storage=post_image_storage,
                                upload_to=upload_to_post_image_directory,
                                width_field='width',
                                height_field='height',
                                blank=False, null=True, format='JPEG', options={'quality': 80},
                                processors=[ResizeToFit(width=1024, upscale=False)])
    width = models.PositiveIntegerField(editable=False, null=False, blank=False)
    height = models.PositiveIntegerField(editable=False, null=False, blank=False)
    hash = models.CharField(_('hash'), max_length=64, blank=False, null=True)
    thumbnail = ProcessedImageField(verbose_name=_('thumbnail'), storage=post_image_storage,
                                    upload_to=upload_to_post_image_directory,
                                    blank=False, null=True, format='JPEG', options={'quality': 30},
                                    processors=[ResizeToFit(width=1024, upscale=False)])

    media = GenericRelation(PostMedia)

    @classmethod
    def create_post_image(cls, image, post_id):
        hash = sha256sum(file=image.file)
        return cls.objects.create(image=image, post_id=post_id, hash=hash)

    @classmethod
    def create_post_media_image(cls, image, post_id, order):
        hash = sha256sum(file=image.file)
        post_image = cls.objects.create(image=image, post_id=post_id, hash=hash, thumbnail=image)
        PostMedia.create_post_media(type=PostMedia.MEDIA_TYPE_IMAGE,
                                    content_object=post_image,
                                    post_id=post_id, order=order)
        return post_image


class PostVideo(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='videos', null=True)

    hash = models.CharField(_('hash'), max_length=64, blank=False, null=True)

    media = GenericRelation(PostMedia)

    width = models.PositiveIntegerField(editable=False, null=True)
    height = models.PositiveIntegerField(editable=False, null=True)
    duration = models.FloatField(editable=False, null=True)

    file = VideoField(width_field='width', height_field='height',
                      duration_field='duration', storage=post_image_storage,
                      upload_to=upload_to_post_video_directory, blank=False, null=True)

    format_set = GenericRelation(Format)

    thumbnail = ProcessedImageField(verbose_name=_('thumbnail'), storage=post_image_storage,
                                    upload_to=upload_to_post_image_directory,
                                    width_field='thumbnail_width',
                                    height_field='thumbnail_height',
                                    blank=False, null=True, format='JPEG', options={'quality': 30},
                                    processors=[ResizeToFit(width=1024, upscale=False)])

    thumbnail_width = models.PositiveIntegerField(editable=False, null=False, blank=False)
    thumbnail_height = models.PositiveIntegerField(editable=False, null=False, blank=False)

    @classmethod
    def create_post_media_video(cls, file, post_id, order):
        hash = sha256sum(file=file.file)
        video_backend = get_backend()

        if isinstance(file, InMemoryUploadedFile):
            # If its in memory, doing read shouldn't be an issue as the file should be small.
            in_disk_file = write_in_memory_file_to_disk(file)
            thumbnail_path = video_backend.get_thumbnail(video_path=in_disk_file.name, at_time=0.0)
        else:
            thumbnail_path = video_backend.get_thumbnail(video_path=file.file.name, at_time=0.0)

        with open(thumbnail_path, 'rb+') as thumbnail_file:
            post_video = cls.objects.create(file=file, post_id=post_id, hash=hash, thumbnail=File(thumbnail_file), )
        PostMedia.create_post_media(type=PostMedia.MEDIA_TYPE_VIDEO,
                                    content_object=post_video,
                                    post_id=post_id, order=order)
        return post_video


class PostComment(models.Model):
    moderated_object = GenericRelation(ModeratedObject, related_query_name='post_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    created = models.DateTimeField(editable=False, db_index=True)
    modified = models.DateTimeField(db_index=True, default=timezone.now)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts_comments')
    text = models.TextField(_('text'), max_length=settings.POST_COMMENT_MAX_LENGTH, blank=False, null=False,
                            validators=post_comment_text_validators)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, related_name='post_comments')
    is_edited = models.BooleanField(default=False, null=False, blank=False)
    # This only happens if the comment was reported and found with critical severity content
    is_deleted = models.BooleanField(default=False)

    @classmethod
    def create_comment(cls, text, commenter, post, parent_comment=None):
        post_comment = PostComment.objects.create(text=text, commenter=commenter, post=post,
                                                  parent_comment=parent_comment)
        post_comment.language = get_language_for_text(text)
        post_comment.save()

        return post_comment

    @classmethod
    def count_comments_for_post_with_id(cls, post_id):
        count_query = Q(post_id=post_id, parent_comment__isnull=True, is_deleted=False)

        return cls.objects.filter(count_query).count()

    @classmethod
    def get_emoji_counts_for_post_comment_with_id(cls, post_comment_id, emoji_id=None, reactor_id=None):
        return Emoji.get_emoji_counts_for_post_comment_with_id(post_comment_id=post_comment_id, emoji_id=emoji_id,
                                                               reactor_id=reactor_id)

    def count_replies(self):
        return self.replies.count()

    def count_replies_with_user(self, user):
        # Count replies excluding users blocked by authenticated user
        count_query = ~Q(Q(commenter__blocked_by_users__blocker_id=user.pk) | Q(
            commenter__user_blocks__blocked_user_id=user.pk))

        if self.post.community:
            if not user.is_staff_of_community_with_name(community_name=self.post.community.name):
                # Dont retrieve comments except from staff members
                blocked_users_query_staff_members = Q(
                    commenter__communities_memberships__community_id=self.post.community.pk)
                blocked_users_query_staff_members.add(Q(commenter__communities_memberships__is_administrator=True) | Q(
                    commenter__communities_memberships__is_moderator=True), Q.AND)

                count_query.add(~blocked_users_query_staff_members, Q.AND)

            # Don't count items that have been reported and approved by community moderators
            ModeratedObject = get_moderated_object_model()
            count_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

        # Dont count soft deleted items
        count_query.add(Q(is_deleted=False), Q.AND)

        # Dont count items we have reported
        count_query.add(~Q(moderated_object__reports__reporter_id=user.pk), Q.AND)

        return self.replies.filter(count_query).count()

    def reply_to_comment(self, commenter, text):
        post_comment = PostComment.create_comment(text=text, commenter=commenter, post=self.post, parent_comment=self)
        post_comment.language = get_language_for_text(text)
        post_comment.save()

        return post_comment

    def react(self, reactor, emoji_id):
        return PostCommentReaction.create_reaction(reactor=reactor, emoji_id=emoji_id, post_comment=self)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()

        self.modified = timezone.now()

        self.full_clean(exclude=['language'])

        post_comment = super(PostComment, self).save(*args, **kwargs)

        self._process_post_comment_mentions()
        self._process_post_comment_hashtags()

        return post_comment

    def _process_post_comment_mentions(self):
        usernames = extract_usernames_from_string(string=self.text)

        if not usernames:
            self.user_mentions.all().delete()
        else:
            existing_mention_usernames = []
            for existing_mention in self.user_mentions.only('id', 'user__username').all().iterator():
                existing_mention_username = existing_mention.user.username.lower()
                if existing_mention_username not in usernames:
                    existing_mention.delete()
                else:
                    existing_mention_usernames.append(existing_mention_username)

            PostCommentUserMention = get_post_comment_user_mention_model()
            User = get_user_model()

            for username in usernames:
                username = username.lower()
                if username not in existing_mention_usernames:
                    try:
                        user = User.objects.only('id', 'username').get(username__iexact=username)
                        user_can_see_post_comment = user.can_see_post_comment(post_comment=self)
                        user_is_commenter = user.pk == self.commenter_id

                        if not user_can_see_post_comment or user_is_commenter:
                            continue

                        if self.parent_comment:
                            user_is_parent_comment_creator = self.parent_comment.commenter_id == user.pk
                            user_has_replied_before = self.parent_comment.replies.filter(commenter_id=user.pk).exists()

                            if user_has_replied_before or user_is_parent_comment_creator:
                                # Its a reply to a comment, if the user previously replied to the comment
                                # or if he's the creator of the parent comment he will already be alerted of the reply,
                                # no need for mention
                                continue
                        else:
                            user_has_commented_before = self.post.comments.filter(commenter_id=user.pk).exists()
                            if user_has_commented_before:
                                # Its a comment to a post, if the user previously commented on the post
                                # he will already be alerted of the comment, no need for mention
                                continue

                        PostCommentUserMention.create_post_comment_user_mention(user=user, post_comment=self)
                        existing_mention_usernames.append(username)
                    except User.DoesNotExist:
                        pass

    def _process_post_comment_hashtags(self):
        if not self.text:
            self.hashtags.all().delete()
        else:
            hashtags = extract_hashtags_from_string(string=self.text)
            if not hashtags:
                self.hashtags.all().delete()
            else:
                existing_hashtags = []
                for existing_hashtag in self.hashtags.only('id', 'name').all().iterator():
                    if existing_hashtag.name not in hashtags:
                        self.hashtags.remove(existing_hashtag)
                    else:
                        existing_hashtags.append(existing_hashtag.name)

                Hashtag = get_hashtag_model()

                for hashtag in hashtags:
                    hashtag = hashtag.lower()
                    if hashtag not in existing_hashtags:
                        hashtag_obj = Hashtag.get_or_create_hashtag(name=hashtag)
                        self.hashtags.add(hashtag_obj)

    def update_comment(self, text):
        self.text = text
        self.is_edited = True
        self.language = get_language_for_text(text)
        self.save()

    def soft_delete(self):
        self.is_deleted = True
        self.delete_notifications()
        self.save()

    def unsoft_delete(self):
        self.is_deleted = False
        self.save()

    def delete_notifications(self):
        # Delete all post comment notifications
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.objects.filter(post_comment_id=self.pk).delete()

        # Delete all post comments reply notifications
        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        PostCommentReplyNotification.objects.filter(post_comment__parent_comment_id=self.pk).delete()

        # Delete all post comment reaction notifications
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.objects.filter(post_comment_reaction__post_comment_id=self.pk).delete()

        # Delete all post comment reply reaction notifications
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.objects.filter(
            post_comment_reaction__post_comment__parent_comment_id=self.pk).delete()

        # Delete all post comment user mention notifications
        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        PostCommentUserMentionNotification.objects.filter(
            post_comment_user_mention__post_comment__post_id=self.pk).delete()

    def delete_notifications_for_user(self, user):
        # Delete all post comment notifications
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.objects.filter(post_comment_id=self.pk,
                                               notification__owner_id=user.pk).delete()

        # Delete all post comments reply notifications
        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        PostCommentReplyNotification.objects.filter(post_comment__parent_comment_id=self.pk,
                                                    notification__owner_id=user.pk).delete()

        # Delete all post comment reaction notifications
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.objects.filter(post_comment_reaction__post_comment_id=self.pk,
                                                       notification__owner_id=user.pk).delete()

        # Delete all post comment reply reaction notifications
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.objects.filter(
            notification__owner_id=user.pk,
            post_comment_reaction__post_comment__parent_comment_id=self.pk).delete()

        # Delete all post comment user mention notifications
        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        PostCommentUserMentionNotification.objects.filter(
            post_comment_user_mention__post_comment__post_id=self.pk,
            notification__owner_id=user.pk).delete()


class PostReaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    created = models.DateTimeField(editable=False)
    reactor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reactions')
    emoji = models.ForeignKey(Emoji, on_delete=models.CASCADE, related_name='post_reactions')

    class Meta:
        unique_together = ('reactor', 'post',)

    @classmethod
    def create_reaction(cls, reactor, emoji_id, post):
        return PostReaction.objects.create(reactor=reactor, emoji_id=emoji_id, post=post)

    @classmethod
    def count_reactions_for_post_with_id(cls, post_id, reactor_id=None):
        count_query = Q(post_id=post_id, reactor__is_deleted=False)

        if reactor_id:
            count_query.add(Q(reactor_id=reactor_id), Q.AND)

        return cls.objects.filter(count_query).count()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostReaction, self).save(*args, **kwargs)


class PostCommentReaction(models.Model):
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='reactions')
    created = models.DateTimeField(editable=False)
    reactor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_reactions')
    emoji = models.ForeignKey(Emoji, on_delete=models.CASCADE, related_name='post_comment_reactions')

    class Meta:
        unique_together = ('reactor', 'post_comment',)

    @classmethod
    def create_reaction(cls, reactor, emoji_id, post_comment):
        return PostCommentReaction.objects.create(reactor=reactor, emoji_id=emoji_id, post_comment=post_comment)

    @classmethod
    def count_reactions_for_post_with_id(cls, post_comment_id, reactor_id=None):
        count_query = Q(post_comment_id=post_comment_id, reactor__is_deleted=False)

        if reactor_id:
            count_query.add(Q(reactor_id=reactor_id), Q.AND)

        return cls.objects.filter(count_query).count()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostCommentReaction, self).save(*args, **kwargs)


class PostMute(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='mutes')
    muter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_mutes')

    class Meta:
        unique_together = ('post', 'muter',)

    @classmethod
    def create_post_mute(cls, post_id, muter_id):
        return cls.objects.create(post_id=post_id, muter_id=muter_id)


class PostCommentMute(models.Model):
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='mutes')
    muter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_mutes')

    class Meta:
        unique_together = ('post_comment', 'muter',)

    @classmethod
    def create_post_comment_mute(cls, post_comment_id, muter_id):
        return cls.objects.create(post_comment_id=post_comment_id, muter_id=muter_id)


class PostLink(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='links')
    link = models.TextField(max_length=settings.POST_MAX_LENGTH)
    has_preview = models.BooleanField(default=False)

    @classmethod
    def create_link(cls, link, post_id):
        return cls.objects.create(link=link, post_id=post_id)

    def refresh_has_preview(self):
        try:
            self.has_preview = peekalink_client.is_peekable(self.link)
        except Exception as e:
            # We dont care whether it succeeded or not
            self.has_preview = False

        self.save()

class PostUserMention(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_mentions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_mentions')

    class Meta:
        unique_together = ('user', 'post',)

    @classmethod
    def create_post_user_mention(cls, user, post):
        post_user_mention = cls.objects.create(user=user, post=post)
        PostUserMentionNotification = get_post_user_mention_notification_model()
        PostUserMentionNotification.create_post_user_mention_notification(post_user_mention_id=post_user_mention.pk,
                                                                          owner_id=user.pk)
        send_post_user_mention_push_notification(post_user_mention=post_user_mention)
        return post_user_mention


class PostCommentUserMention(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_mentions')
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='user_mentions')

    class Meta:
        unique_together = ('user', 'post_comment',)

    @classmethod
    def create_post_comment_user_mention(cls, user, post_comment):
        post_comment_user_mention = cls.objects.create(user=user, post_comment=post_comment)
        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        PostCommentUserMentionNotification.create_post_comment_user_mention_notification(
            post_comment_user_mention_id=post_comment_user_mention.pk,
            owner_id=user.pk)
        send_post_comment_user_mention_push_notification(post_comment_user_mention=post_comment_user_mention)
        return post_comment_user_mention
