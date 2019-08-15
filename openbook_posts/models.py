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

from openbook_common.models import Emoji, Language
from openbook_common.utils.helpers import delete_file_field, sha256sum, extract_usernames_from_string
from openbook_common.utils.model_loaders import get_emoji_model, \
    get_circle_model, get_community_model, get_post_comment_notification_model, \
    get_post_comment_reply_notification_model, get_post_reaction_notification_model, get_moderated_object_model, \
    get_post_user_mention_notification_model, get_post_comment_user_mention_notification_model, get_user_model, \
    get_post_user_mention_model, get_post_comment_user_mention_model
from imagekit.models import ProcessedImageField

from openbook_moderation.models import ModeratedObject
from openbook_notifications.helpers import send_post_comment_user_mention_push_notification, \
    send_post_user_mention_push_notification
from openbook_posts.helpers import upload_to_post_image_directory, upload_to_post_video_directory
from openbook_common.helpers import get_language_for_text


class Post(models.Model):
    moderated_object = GenericRelation(ModeratedObject, related_query_name='posts')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    text = models.TextField(_('text'), max_length=settings.POST_MAX_LENGTH, blank=False, null=True)
    created = models.DateTimeField(editable=False, db_index=True)
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
            post.language = get_language_for_text(text)

        if image:
            PostImage.create_post_image(image=image, post_id=post.pk)

        if video:
            PostVideo.create_post_video(video=video, post_id=post.pk)

        if circles_ids:
            post.circles.add(*circles_ids)
        else:
            Community = get_community_model()
            post.community = Community.objects.get(name=community_name)

        post.save()

        return post

    @classmethod
    def get_emoji_counts_for_post_with_id(cls, post_id, emoji_id=None, reactor_id=None):
        Emoji = get_emoji_model()
        return Emoji.get_emoji_counts_for_post_with_id(post_id=post_id, emoji_id=emoji_id, reactor_id=reactor_id)

    @classmethod
    def get_trending_posts_for_user_with_id(cls, user_id):
        trending_posts_query = cls._get_trending_posts_query()
        trending_posts_query.add(~Q(community__banned_users__id=user_id), Q.AND)
        trending_posts_query.add(Q(is_closed=False, is_deleted=False), Q.AND)

        trending_posts_query.add(~Q(Q(creator__blocked_by_users__blocker_id=user_id) | Q(
            creator__user_blocks__blocked_user_id=user_id)), Q.AND)

        trending_posts_query.add(~Q(moderated_object__reports__reporter_id=user_id), Q.AND)

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

        if post_commenter.pk == post.creator_id:
            result = other_commenters
        else:
            post_creator = User.objects.filter(pk=post.creator_id)
            result = other_commenters.union(post_creator)

        return result

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

        if parent_post_comment.commenter_id == post_commenter.pk:
            result = other_repliers
        else:
            # Add post comment creator
            post_comment_creator = User.objects.filter(pk=parent_post_comment.commenter_id)
            result = other_repliers.union(post_comment_creator)

        return result

    def count_comments(self):
        return PostComment.count_comments_for_post_with_id(self.pk)

    def count_comments_with_user(self, user):
        # Only count top level comments
        count_query = Q(parent_comment__isnull=True)

        if self.community:
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
        self.language = get_language_for_text(text)
        self.save()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id and not self.created:
            self.created = timezone.now()

        post = super(Post, self).save(*args, **kwargs)

        self._process_post_mentions()

        return post

    def delete(self, *args, **kwargs):
        self.delete_media()
        super(Post, self).delete(*args, **kwargs)

    def delete_media(self):
        if self.has_video():
            delete_file_field(self.video.video)

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
        # Remove all post comment notifications
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.objects.filter(post_comment__post_id=self.pk).delete()

        # Remove all post reaction notifications
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.objects.filter(post_reaction__post_id=self.pk).delete()

        # Remove all post comment reply notifications
        PostCommentReplyNotification = get_post_comment_notification_model()
        PostCommentReplyNotification.objects.filter(post_comment__post_id=self.pk).delete()

        # Remove all post user mention notifications
        PostUserMentionNotification = get_post_user_mention_notification_model()
        PostUserMentionNotification.objects.filter(post_user_mention__post_id=self.pk).delete()

    def delete_notifications_for_user(self, user):
        # Remove all post comment notifications
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.objects.filter(post_comment__post_id=self.pk,
                                               notification__owner_id=user.pk).delete()

        # Remove all post reaction notifications
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.objects.filter(post_reaction__post_id=self.pk,
                                                notification__owner_id=user.pk).delete()

        # Remove all post comment reply notifications
        PostCommentReplyNotification = get_post_comment_notification_model()
        PostCommentReplyNotification.objects.filter(post_comment__post=self.pk,
                                                    notification__owner_id=user.pk).delete()

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
                    if existing_mention.user.username not in usernames:
                        existing_mention.delete()
                    else:
                        existing_mention_usernames = existing_mention.user.username

                PostUserMention = get_post_user_mention_model()
                User = get_user_model()

                for username in usernames:
                    username = username.lower()
                    if username not in existing_mention_usernames:
                        try:
                            user = User.objects.only('id', 'username').get(username=username)
                            user_is_post_creator = user.pk == self.creator_id
                            if user.can_see_post(post=self) and not user_is_post_creator:
                                PostUserMention.create_post_user_mention(user=user, post=self)
                                existing_mention_usernames.append(username)
                        except User.DoesNotExist:
                            pass

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
                                blank=False, null=True, format='JPEG', options={'quality': 100},
                                processors=[ResizeToFit(width=1024, upscale=False)])
    width = models.PositiveIntegerField(editable=False, null=False, blank=False)
    height = models.PositiveIntegerField(editable=False, null=False, blank=False)
    hash = models.CharField(_('hash'), max_length=64, blank=False, null=True)

    @classmethod
    def create_post_image(cls, image, post_id):
        hash = sha256sum(file=image.file)
        return cls.objects.create(image=image, post_id=post_id, hash=hash)


class PostVideo(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='video')
    video = models.FileField(_('video'), blank=False, null=False, storage=post_image_storage,
                             upload_to=upload_to_post_video_directory)
    hash = models.CharField(_('hash'), max_length=64, blank=False, null=True)

    @classmethod
    def create_post_video(cls, video, post_id):
        hash = sha256sum(file=video.file)
        return cls.objects.create(video=video, post_id=post_id, hash=hash)


class PostComment(models.Model):
    moderated_object = GenericRelation(ModeratedObject, related_query_name='post_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    created = models.DateTimeField(editable=False, db_index=True)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts_comments')
    text = models.TextField(_('text'), max_length=settings.POST_COMMENT_MAX_LENGTH, blank=False, null=False)
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
        count_query = Q()

        if self.post.community_id:
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

        self._process_post_comment_mentions()
        return super(PostComment, self).save(*args, **kwargs)

    def _process_post_comment_mentions(self):
        usernames = extract_usernames_from_string(string=self.text)

        if not usernames:
            self.user_mentions.all().delete()
        else:
            existing_mention_usernames = []
            for existing_mention in self.user_mentions.only('id', 'user__username').all().iterator():
                if existing_mention.user.username not in usernames:
                    existing_mention.delete()
                else:
                    existing_mention_usernames = existing_mention.user.username

            PostCommentUserMention = get_post_comment_user_mention_model()
            User = get_user_model()

            for username in usernames:
                username = username.lower()
                if username not in existing_mention_usernames:
                    try:
                        user = User.objects.only('id', 'username').get(username=username)
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
        # Delete all post comment reply notifications
        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        PostCommentReplyNotification.delete_post_comment_reply_notifications(post_comment_id=self.pk)

        # Delete all post comment user mention notifications
        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        PostCommentUserMentionNotification.objects.filter(
            post_comment_user_mention__post_comment__post_id=self.pk).delete()

    def delete_notifications_for_user(self, user):
        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        PostCommentReplyNotification.delete_post_comment_reply_notification(post_comment_id=self.pk, owner_id=user.pk)
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.delete_post_comment_notification(post_comment_id=self.pk, owner_id=user.pk)


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
