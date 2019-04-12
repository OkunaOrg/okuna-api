import secrets
from datetime import datetime, timedelta
import re
import jwt
import uuid
from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import six
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from imagekit.models import ProcessedImageField
from pilkit.processors import ResizeToFill, ResizeToFit
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied, AuthenticationFailed
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives

from openbook.settings import USERNAME_MAX_LENGTH
from openbook_auth.helpers import upload_to_user_cover_directory, upload_to_user_avatar_directory
from openbook_common.models import Badge
from openbook_common.utils.helpers import delete_file_field
from openbook_common.utils.model_loaders import get_connection_model, get_circle_model, get_follow_model, \
    get_post_model, get_list_model, get_post_comment_model, get_post_reaction_model, \
    get_emoji_group_model, get_user_invite_model, get_community_model, get_community_invite_model, get_tag_model, \
    get_post_comment_notification_model, get_follow_notification_model, get_connection_confirmed_notification_model, \
    get_connection_request_notification_model, get_post_reaction_notification_model, get_device_model, \
    get_post_mute_model, get_community_invite_notification_model
from openbook_common.validators import name_characters_validator
from openbook_notifications.push_notifications import senders


class User(AbstractUser):
    """"
    Custom user model to change behaviour of the default user model
    such as validation and required fields.
    """
    first_name = None
    last_name = None
    email = models.EmailField(_('email address'), unique=True, null=False, blank=False)
    connections_circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.CASCADE, related_name='+',
                                           null=True, blank=True)

    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()
    is_email_verified = models.BooleanField(default=False)

    username = models.CharField(
        _('username'),
        blank=False,
        null=False,
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        help_text=_('Required. %(username_max_length)d characters or fewer. Letters, digits and _ only.' % {
            'username_max_length': USERNAME_MAX_LENGTH}),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    JWT_TOKEN_TYPE_CHANGE_EMAIL = 'CE'
    JWT_TOKEN_TYPE_PASSWORD_RESET = 'PR'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @classmethod
    def create_user(cls, username, email=None, password=None, name=None, avatar=None, is_of_legal_age=None,
                    badge=None, **extra_fields):
        new_user = cls.objects.create_user(username, email=email, password=password, **extra_fields)
        user_profile = bootstrap_user_profile(name=name, user=new_user, avatar=avatar,
                                              is_of_legal_age=is_of_legal_age)

        if badge:
            user_profile.badges.add(badge)

        return new_user

    @classmethod
    def is_username_taken(cls, username):
        UserInvite = get_user_invite_model()
        user_invites = UserInvite.objects.filter(username=username, created_user=None)
        users = cls.objects.filter(username=username)
        if not user_invites.exists() and not users.exists():
            return False
        return True

    @classmethod
    def is_email_taken(cls, email):
        try:
            cls.objects.get(email=email)
            return True
        except User.DoesNotExist:
            return False

    @classmethod
    def get_public_posts_for_user_with_username(cls, username, max_id=None):
        Circle = get_circle_model()
        world_circle_id = Circle.get_world_circle_id()

        final_query = Q(creator__username=username, circles__id=world_circle_id)

        if max_id:
            final_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()
        result = Post.objects.filter(final_query)

        return result

    @classmethod
    def get_user_with_username(cls, user_username):
        return cls.objects.get(username=user_username)

    @classmethod
    def get_user_with_email(cls, user_email):
        return cls.objects.get(email=user_email)

    @classmethod
    def sanitise_username(cls, username):
        chars = '[@#!±$%^&*()=|/><?,:;\~`{}]'
        return re.sub(chars, '', username).lower().replace(' ', '_').replace('+', '_').replace('-', '_')

    @classmethod
    def get_temporary_username(cls, email):
        username = email.split('@')[0]
        temp_username = cls.sanitise_username(username)
        while cls.is_username_taken(temp_username):
            temp_username = username + str(secrets.randbelow(9999))

        return temp_username

    @classmethod
    def get_public_users_with_query(cls, query):
        users_query = Q(username__icontains=query)
        users_query.add(Q(profile__name__icontains=query), Q.OR)
        return cls.objects.filter(users_query)

    @classmethod
    def get_user_for_password_reset_token(cls, password_verification_token):
        try:
            token_contents = jwt.decode(password_verification_token, settings.SECRET_KEY,
                                        algorithm=settings.JWT_ALGORITHM)

            token_user_id = token_contents['user_id']
            token_type = token_contents['type']

            if token_type != cls.JWT_TOKEN_TYPE_PASSWORD_RESET:
                raise ValidationError(
                    _('Token type does not match')
                )
            user = User.objects.get(pk=token_user_id)

            return user
        except jwt.InvalidSignatureError:
            raise ValidationError(
                _('Invalid token signature')
            )
        except jwt.ExpiredSignatureError:
            raise ValidationError(
                _('Token expired')
            )
        except jwt.DecodeError:
            raise ValidationError(
                _('Failed to decode token')
            )
        except User.DoesNotExist:
            raise ValidationError(
                _('No user found for token')
            )
        except KeyError:
            raise ValidationError(
                _('Invalid token')
            )

    def count_posts(self):
        return self.posts.count()

    def count_unread_notifications(self):
        return self.notifications.filter(read=False).count()

    def count_public_posts(self):
        """
        Count how many public posts has the user created
        :return:
        """
        world_circle_id = self._get_world_circle_id()

        return self.posts.filter(circles__id=world_circle_id).count()

    def count_posts_for_user_with_id(self, id):
        """
        Count how many posts has the user created relative to another user
        :param id:
        :return: count
        """
        user = User.objects.get(pk=id)
        if user.is_connected_with_user_with_id(self.pk):
            count = user.get_posts_for_user_with_username(username=self.username).count()
        else:
            count = self.count_public_posts()
        return count

    def count_followers(self):
        Follow = get_follow_model()
        return Follow.objects.filter(followed_user__id=self.pk).count()

    def count_following(self):
        return self.follows.count()

    def count_connections(self):
        return self.connections.count()

    def delete_with_password(self, password):
        self._check_password_matches(password=password)
        self.delete()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(User, self).save(*args, **kwargs)

    def update_profile_cover(self, cover, save=True):
        if cover is None:
            self.delete_profile_cover(save=False)
        else:
            self.profile.cover = cover

        if save:
            self.profile.save()

    def delete_profile_cover(self, save=True):
        delete_file_field(self.profile.cover)
        self.profile.cover = None
        self.profile.cover.delete(save=save)

    def update_profile_avatar(self, avatar, save=True):
        if avatar is None:
            self.delete_profile_avatar(save=False)
        else:
            self.profile.avatar = avatar

        if save:
            self.profile.save()

    def delete_profile_avatar(self, save=True):
        delete_file_field(self.profile.avatar)
        self.profile.avatar = None
        self.profile.avatar.delete(save=save)

    def update_username(self, username):
        self._check_username_not_taken(username)
        self.username = username
        self.save()

    def update_password(self, password):
        self.set_password(password)
        self.save()

    def request_email_update(self, email):
        self._check_email_not_taken(email)
        self.save()
        verify_token = self._make_email_verification_token_for_email(new_email=email)
        return verify_token

    def verify_email_with_token(self, token):
        new_email = self._check_email_verification_token_is_valid_for_email(email_verification_token=token)
        self.email = new_email
        self.save()

    def verify_password_reset_token(self, token, password):
        self._check_password_reset_verification_token_is_valid(password_verification_token=token)
        self.update_password(password=password)

    def request_password_reset(self):
        password_reset_token = self._make_password_reset_verification_token()
        self._send_password_reset_email_with_token(password_reset_token)
        return password_reset_token

    def update(self,
               username=None,
               name=None,
               location=None,
               bio=None,
               url=None,
               followers_count_visible=None,
               save=True):

        profile = self.profile

        if username:
            self.update_username(username)

        if url is not None:
            if len(url) == 0:
                profile.url = None
            else:
                profile.url = url

        if name:
            profile.name = name

        if location is not None:
            if len(location) == 0:
                profile.location = None
            else:
                profile.location = location

        if bio is not None:
            if len(bio) == 0:
                profile.bio = None
            else:
                profile.bio = bio

        if followers_count_visible is not None:
            profile.followers_count_visible = followers_count_visible

        if save:
            profile.save()
            self.save()

    def update_notifications_settings(self, post_comment_notifications=None, post_reaction_notifications=None,
                                      follow_notifications=None, connection_request_notifications=None,
                                      connection_confirmed_notifications=None,
                                      community_invite_notifications=None):

        notifications_settings = self.notifications_settings
        notifications_settings.update(
            post_comment_notifications=post_comment_notifications,
            post_reaction_notifications=post_reaction_notifications,
            follow_notifications=follow_notifications,
            connection_request_notifications=connection_request_notifications,
            connection_confirmed_notifications=connection_confirmed_notifications,
            community_invite_notifications=community_invite_notifications
        )
        return notifications_settings

    def is_fully_connected_with_user_with_id(self, user_id):
        if not self.is_connected_with_user_with_id(user_id):
            return False

        connection = self.connections.filter(
            target_connection__user_id=user_id).get()

        target_connection = connection.target_connection

        # If both connections have circles on them, we're fully connected
        if target_connection.circles.all().exists() and connection.circles.all().exists():
            return True

        return False

    def is_pending_confirm_connection_for_user_with_id(self, user_id):
        if not self.is_connected_with_user_with_id(user_id):
            return False

        connection = self.connections.filter(
            target_connection__user_id=user_id).get()

        return not connection.circles.exists()

    def is_connected_with_user(self, user):
        return self.is_connected_with_user_with_id(user.pk)

    def is_connected_with_user_with_id(self, user_id):
        return self.connections.select_related('target_connection__user_id').filter(
            target_connection__user_id=user_id).exists()

    def is_connected_with_user_with_username(self, username):
        count = self.connections.select_related('target_connection__user__username').filter(
            target_connection__user__username=username).count()
        return count > 0

    def is_connected_with_user_in_circle(self, user, circle):
        return self.is_connected_with_user_with_id_in_circle_with_id(user.pk, circle.pk)

    def is_connected_with_user_with_id_in_circle_with_id(self, user_id, circle_id):
        return self.connections.select_related('target_connection__user_id').filter(
            target_connection__user_id=user_id,
            circles__id=circle_id).exists()

    def is_connected_with_user_in_circles(self, user, circles):
        circles_ids = [circle.pk for circle in circles]
        return self.is_connected_with_user_with_id_in_circles_with_ids(user.pk, circles_ids)

    def is_connected_with_user_with_id_in_circles_with_ids(self, user_id, circles_ids):
        count = self.connections.filter(
            target_connection__user_id=user_id,
            circles__id__in=circles_ids).count()
        return count > 0

    def is_following_user(self, user):
        return self.is_following_user_with_id(user.pk)

    def is_following_user_with_id(self, user_id):
        return self.follows.filter(followed_user__id=user_id).exists()

    def is_following_user_with_username(self, user_username):
        return self.follows.filter(followed_user__username=user_username).exists()

    def is_following_user_in_list(self, user, list):
        return self.is_following_user_with_id_in_list_with_id(user.pk, list.pk)

    def is_following_user_with_id_in_list_with_id(self, user_id, list_id):
        return self.follows.filter(
            followed_user_id=user_id,
            lists__id=list_id).count() == 1

    def is_world_circle_id(self, id):
        world_circle_id = self._get_world_circle_id()
        return world_circle_id == id

    def is_connections_circle_id(self, id):
        return self.connections_circle_id == id

    def has_circle_with_id(self, circle_id):
        return self.circles.filter(id=circle_id).exists()

    def has_circle_with_name(self, circle_name):
        return self.circles.filter(name=circle_name).exists()

    def has_post_with_id(self, post_id):
        return self.posts.filter(id=post_id).exists()

    def has_muted_post_with_id(self, post_id):
        return self.post_mutes.filter(post_id=post_id).exists()

    def has_circles_with_ids(self, circles_ids):
        return self.circles.filter(id__in=circles_ids).count() == len(circles_ids)

    def has_list_with_id(self, list_id):
        return self.lists.filter(id=list_id).count() > 0

    def has_invited_user_with_username_to_community_with_name(self, username, community_name):
        return self.created_communities_invites.filter(invited_user__username=username,
                                                       community__name=community_name).exists()

    def is_administrator_of_community_with_name(self, community_name):
        return self.communities_memberships.filter(community__name=community_name, is_administrator=True).exists()

    def is_member_of_communities(self):
        return self.communities_memberships.all().exists()

    def is_member_of_community_with_name(self, community_name):
        return self.communities_memberships.filter(community__name=community_name).exists()

    def is_banned_from_community_with_name(self, community_name):
        return self.banned_of_communities.filter(name=community_name).exists()

    def is_creator_of_community_with_name(self, community_name):
        return self.created_communities.filter(name=community_name).exists()

    def is_moderator_of_community_with_name(self, community_name):
        return self.communities_memberships.filter(community__name=community_name, is_moderator=True).exists()

    def is_invited_to_community_with_name(self, community_name):
        Community = get_community_model()
        return Community.is_user_with_username_invited_to_community_with_name(username=self.username,
                                                                              community_name=community_name)

    def has_favorite_community_with_name(self, community_name):
        return self.favorite_communities.filter(name=community_name).exists()

    def has_list_with_name(self, list_name):
        return self.lists.filter(name=list_name).count() > 0

    def has_lists_with_ids(self, lists_ids):
        return self.lists.filter(id__in=lists_ids).count() == len(lists_ids)

    def has_reacted_to_post_with_id(self, post_id, emoji_id=None):
        has_reacted_query = Q(post_id=post_id)

        if emoji_id:
            has_reacted_query.add(Q(emoji_id=emoji_id), Q.AND)

        return self.post_reactions.filter(has_reacted_query).count() > 0

    def has_commented_post_with_id(self, post_id):
        return self.posts_comments.filter(post_id=post_id).exists()

    def has_notification_with_id(self, notification_id):
        return self.notifications.filter(pk=notification_id).exists()

    def has_device_with_uuid(self, device_uuid):
        return self.devices.filter(uuid=device_uuid).exists()

    def has_follow_notifications_enabled(self):
        return self.notifications_settings.follow_notifications

    def has_reaction_notifications_enabled_for_post_with_id(self, post_id):
        return self.notifications_settings.post_reaction_notifications and not self.has_muted_post_with_id(
            post_id=post_id)

    def has_comment_notifications_enabled_for_post_with_id(self, post_id):
        return self.notifications_settings.post_comment_notifications and not self.has_muted_post_with_id(
            post_id=post_id)

    def has_connection_request_notifications_enabled(self):
        return self.notifications_settings.connection_request_notifications

    def has_community_invite_notifications_enabled(self):
        return self.notifications_settings.community_invite_notifications

    def has_connection_confirmed_notifications_enabled(self):
        return self.notifications_settings.connection_confirmed_notifications

    def get_lists_for_follow_for_user_with_id(self, user_id):
        self._check_is_following_user_with_id(user_id)
        follow = self.get_follow_for_user_with_id(user_id)
        return follow.lists

    def get_circles_for_connection_with_user_with_id(self, user_id):
        self._check_is_connected_with_user_with_id(user_id)
        connection = self.get_connection_for_user_with_id(user_id)
        return connection.circles

    def get_reaction_for_post_with_id(self, post_id):
        return self.post_reactions.filter(post_id=post_id).get()

    def get_reactions_for_post_with_id(self, post_id, max_id=None, emoji_id=None):
        self._check_can_get_reactions_for_post_with_id(post_id)
        reactions_query = Q(post_id=post_id)
        Post = get_post_model()

        # If reactions are private, return only own reactions
        if not Post.post_with_id_has_public_reactions(post_id):
            reactions_query = Q(reactor_id=self.pk)

        if max_id:
            reactions_query.add(Q(id__lt=max_id), Q.AND)

        if emoji_id:
            reactions_query.add(Q(emoji_id=emoji_id), Q.AND)

        PostReaction = get_post_reaction_model()
        return PostReaction.objects.filter(reactions_query)

    def get_reactions_count_for_post_with_id(self, post_id):
        commenter_id = None

        Post = get_post_model()

        # If reactions are private, count only own reactions
        if not Post.post_with_id_has_public_reactions(post_id):
            commenter_id = self.pk

        PostReaction = get_post_reaction_model()

        return PostReaction.count_reactions_for_post_with_id(post_id, commenter_id=commenter_id)

    def get_emoji_counts_for_post_with_id(self, post_id, emoji_id=None):
        self._check_can_get_reactions_for_post_with_id(post_id)
        Post = get_post_model()

        reactor_id = None

        # If reactions are private count only own reactions
        if not Post.post_with_id_has_public_reactions(post_id):
            reactor_id = self.pk

        return Post.get_emoji_counts_for_post_with_id(post_id, emoji_id=emoji_id, reactor_id=reactor_id)

    def react_to_post_with_id(self, post_id, emoji_id, emoji_group_id):
        self._check_can_react_to_post_with_id(post_id)
        self._check_can_react_with_emoji_id_and_emoji_group_id(emoji_id, emoji_group_id)

        if self.has_reacted_to_post_with_id(post_id):
            post_reaction = self.post_reactions.get(post_id=post_id)
            post_reaction.emoji_id = emoji_id
            post_reaction.save()
        else:
            Post = get_post_model()
            post = Post.objects.filter(pk=post_id).get()
            post_reaction = post.react(reactor=self, emoji_id=emoji_id)
            if post_reaction.post.creator_id != self.pk:
                # TODO Refactor. This check is being done twice. (Also in _send_post_reaction_push_notification)
                if post.creator.has_reaction_notifications_enabled_for_post_with_id(post_id=post.pk):
                    self._create_post_reaction_notification(post_reaction=post_reaction)
                self._send_post_reaction_push_notification(post_reaction=post_reaction)

        return post_reaction

    def delete_reaction_with_id_for_post_with_id(self, post_reaction_id, post_id):
        self._check_can_delete_reaction_with_id_for_post_with_id(post_reaction_id, post_id)
        PostReaction = get_post_reaction_model()
        post_reaction = PostReaction.objects.filter(pk=post_reaction_id).get()
        self._delete_post_reaction_notification(post_reaction=post_reaction)
        post_reaction.delete()

    def get_comments_for_post_with_id(self, post_id, min_id=None, max_id=None):
        comments_query = Q(post_id=post_id)

        if max_id:
            comments_query.add(Q(id__lt=max_id), Q.AND)
        elif min_id:
            comments_query.add(Q(id__gte=min_id), Q.AND)

        Post = get_post_model()
        # If comments are private, return only own comments
        if not Post.post_with_id_has_public_comments(post_id):
            comments_query.add(Q(commenter_id=self.pk), Q.AND)

        PostComment = get_post_comment_model()
        return PostComment.objects.filter(comments_query)

    def get_comments_count_for_post_with_id(self, post_id):
        commenter_id = None

        Post = get_post_model()

        # If comments are private, count only own comments
        # TODO If its our post we need to circumvent this too
        if not Post.post_with_id_has_public_comments(post_id):
            commenter_id = self.pk

        PostComment = get_post_comment_model()

        return PostComment.count_comments_for_post_with_id(post_id, commenter_id=commenter_id)

    def comment_post_with_id(self, post_id, text):
        self._check_can_comment_in_post_with_id(post_id)
        Post = get_post_model()
        post = Post.objects.filter(pk=post_id).get()
        post_comment = post.comment(text=text, commenter=self)
        post_creator = post.creator
        post_commenter = self

        post_notification_target_users = Post.get_post_comment_notification_target_users(post_id=post.id,
                                                                                         post_commenter_id=self.pk)
        PostCommentNotification = get_post_comment_notification_model()

        for post_notification_target_user in post_notification_target_users:

            post_notification_target_user_is_post_creator = post_notification_target_user.id == post_creator.id
            post_notification_target_has_comment_notifications_enabled = post_notification_target_user.has_comment_notifications_enabled_for_post_with_id(
                post_id=post_comment.post_id)

            if post_notification_target_has_comment_notifications_enabled:
                PostCommentNotification.create_post_comment_notification(post_comment_id=post_comment.pk,
                                                                         owner_id=post_notification_target_user.id)

                if post_notification_target_user_is_post_creator:
                    notification_message = {
                        "en": _('@%(post_commenter_username)s commented on your post.') % {
                            'post_commenter_username': post_commenter.username
                        }}
                else:
                    notification_message = {
                        "en": _('@%(post_commenter_username)s commented on a post you also commented on.') % {
                            'post_commenter_username': post_commenter.username
                        }}

                self._send_post_comment_push_notification(post_comment=post_comment,
                                                          notification_message=notification_message,
                                                          notification_target_user=post_notification_target_user)

        return post_comment

    def delete_comment_with_id_for_post_with_id(self, post_comment_id, post_id):
        self._check_can_delete_comment_with_id_for_post_with_id(post_comment_id, post_id)
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        self._delete_post_comment_notification(post_comment=post_comment)
        post_comment.delete()

    def update_comment_with_id_for_post_with_id(self, post_comment_id, post_id, text):
        self.has_post_comment_with_id(post_comment_id)
        self._check_can_edit_comment_with_id_for_post_with_id(post_comment_id, post_id)
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        post_comment.text = text
        post_comment.is_edited = True
        post_comment.save()
        return post_comment

    def has_post_comment_with_id(self, post_comment_id):
        self._check_has_post_comment_with_id(post_comment_id)

    def create_circle(self, name, color):
        self._check_circle_name_not_taken(name)
        Circle = get_circle_model()
        circle = Circle.objects.create(name=name, creator=self, color=color)

        return circle

    def delete_circle(self, circle):
        return self.delete_circle_with_id(circle.pk)

    def delete_circle_with_id(self, circle_id):
        self._check_can_delete_circle_with_id(circle_id)
        circle = self.circles.get(id=circle_id)
        circle.delete()

    def update_circle(self, circle, **kwargs):
        return self.update_circle_with_id(circle.pk, **kwargs)

    def update_circle_with_id(self, circle_id, name=None, color=None, usernames=None):
        self._check_can_update_circle_with_id(circle_id)
        self._check_circle_data(name, color)
        circle_to_update = self.circles.get(id=circle_id)

        if name:
            circle_to_update.name = name

        if color:
            circle_to_update.color = color

        if isinstance(usernames, list):
            # TODO This is a goddamn expensive operation. Improve.
            new_circle_users = []

            circle_users = circle_to_update.users
            circle_users_by_username = {}

            for circle_user in circle_users:
                circle_user_username = circle_user.username
                circle_users_by_username[circle_user_username] = circle_user

            for username in usernames:
                user = User.objects.get(username=username)
                user_exists_in_circle = username in circle_users_by_username
                if user_exists_in_circle:
                    # The username added might not be same person we had before
                    new_circle_users.append(circle_users_by_username[username])
                else:
                    new_circle_users.append(user)

            circle_users_to_remove = filter(lambda circle_user: circle_user not in new_circle_users, circle_users)

            for user_to_remove in circle_users_to_remove:
                self.remove_circle_with_id_from_connection_with_user_with_id(user_to_remove.pk, circle_to_update.pk)

            for new_circle_user in new_circle_users:
                if not self.is_connected_with_user_with_id_in_circle_with_id(new_circle_user.pk, circle_to_update.pk):
                    if self.is_connected_with_user_with_id(new_circle_user.pk):
                        self.add_circle_with_id_to_connection_with_user_with_id(new_circle_user.pk, circle_to_update.pk)
                    else:
                        self.connect_with_user_with_id(new_circle_user.pk, circles_ids=[circle_to_update.pk])

        circle_to_update.save()
        return circle_to_update

    def remove_circle_with_id_from_connection_with_user_with_id(self, user_id, circle_id):
        self._check_is_following_user_with_id(user_id)
        self._check_is_connected_with_user_with_id_in_circle_with_id(user_id, circle_id)
        connection = self.get_connection_for_user_with_id(user_id)
        connection.circles.remove(circle_id)
        return connection

    def add_circle_with_id_to_connection_with_user_with_id(self, user_id, circle_id):
        self._check_is_following_user_with_id(user_id)
        self._check_is_not_connected_with_user_with_id_in_circle_with_id(user_id, circle_id)
        connection = self.get_connection_for_user_with_id(user_id)
        connection.circles.add(circle_id)
        return connection

    def get_circle_with_id(self, circle_id):
        self._check_can_get_circle_with_id(circle_id)
        return self.circles.get(id=circle_id)

    def favorite_community_with_name(self, community_name):
        self._check_can_favorite_community_with_name(community_name=community_name)

        Community = get_community_model()
        community_to_favorite = Community.objects.get(name=community_name)

        self.favorite_communities.add(community_to_favorite)

        return community_to_favorite

    def unfavorite_community_with_name(self, community_name):
        self._check_can_unfavorite_community_with_name(community_name=community_name)

        Community = get_community_model()
        community_to_unfavorite = Community.objects.get(name=community_name)

        self.favorite_communities.remove(community_to_unfavorite)

        return community_to_unfavorite

    def create_community(self, name, title, type, color, categories_names, description=None, rules=None,
                         avatar=None, cover=None, user_adjective=None, users_adjective=None,
                         invites_enabled=None):
        self._check_can_create_community_with_name(name=name)

        Community = get_community_model()
        community = Community.create_community(name=name, creator=self, title=title, description=description,
                                               rules=rules, cover=cover, type=type, avatar=avatar, color=color,
                                               user_adjective=user_adjective, users_adjective=users_adjective,
                                               categories_names=categories_names,
                                               invites_enabled=invites_enabled)

        return community

    def delete_community(self, community):
        return self.delete_community_with_name(community.name)

    def delete_community_with_name(self, community_name):
        self._check_can_delete_community_with_name(community_name)

        Community = get_community_model()
        community = Community.objects.get(name=community_name)

        community.delete()

    def update_community(self, community, title=None, name=None, description=None, color=None, type=None,
                         user_adjective=None,
                         users_adjective=None, rules=None):
        return self.update_community_with_name(community.name, name=name, title=title, description=description,
                                               color=color, type=type, user_adjective=user_adjective,
                                               users_adjective=users_adjective, rules=rules)

    def update_community_with_name(self, community_name, title=None, name=None, description=None, color=None, type=None,
                                   user_adjective=None,
                                   users_adjective=None, rules=None, categories_names=None,
                                   invites_enabled=None):
        self._check_can_update_community_with_name(community_name)
        self._check_community_data(name)

        Community = get_community_model()
        community_to_update = Community.objects.get(name=community_name)

        community_to_update.update(name=name, title=title, description=description,
                                   color=color, type=type, user_adjective=user_adjective,
                                   users_adjective=users_adjective, rules=rules, categories_names=categories_names,
                                   invites_enabled=invites_enabled)

        return community_to_update

    def update_community_with_name_avatar(self, community_name, avatar):
        self._check_can_update_community_with_name(community_name)
        self._check_community_data(avatar=avatar)

        Community = get_community_model()
        community_to_update_avatar_from = Community.objects.get(name=community_name)
        community_to_update_avatar_from.avatar = avatar

        community_to_update_avatar_from.save()

        return community_to_update_avatar_from

    def delete_community_with_name_avatar(self, community_name):
        self._check_can_update_community_with_name(community_name)
        Community = get_community_model()
        community_to_delete_avatar_from = Community.objects.get(name=community_name)
        delete_file_field(community_to_delete_avatar_from.avatar)
        community_to_delete_avatar_from.avatar = None
        community_to_delete_avatar_from.save()
        return community_to_delete_avatar_from

    def update_community_with_name_cover(self, community_name, cover):
        self._check_can_update_community_with_name(community_name)
        self._check_community_data(cover=cover)

        Community = get_community_model()
        community_to_update_cover_from = Community.objects.get(name=community_name)

        community_to_update_cover_from.cover = cover

        community_to_update_cover_from.save()

        return community_to_update_cover_from

    def delete_community_with_name_cover(self, community_name):
        self._check_can_update_community_with_name(community_name)

        Community = get_community_model()
        community_to_delete_cover_from = Community.objects.get(name=community_name)

        delete_file_field(community_to_delete_cover_from.cover)
        community_to_delete_cover_from.cover = None
        community_to_delete_cover_from.save()
        return community_to_delete_cover_from

    def get_community_with_name_members(self, community_name, max_id=None, exclude_keywords=None):
        self._check_can_get_community_with_name_members(
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_members(community_name=community_name, members_max_id=max_id,
                                                         exclude_keywords=exclude_keywords)

    def search_community_with_name_members(self, community_name, query, exclude_keywords=None):
        self._check_can_get_community_with_name_members(
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_members(community_name=community_name, query=query,
                                                            exclude_keywords=exclude_keywords)

    def join_community_with_name(self, community_name):
        self._check_can_join_community_with_name(
            community_name=community_name)
        Community = get_community_model()
        community_to_join = Community.objects.get(name=community_name)
        community_to_join.add_member(self)

        # Clean up any invites
        CommunityInvite = get_community_invite_model()
        CommunityInvite.objects.filter(community__name=community_name, invited_user__username=self.username).delete()

        # No need to delete community invite notifications as they are delete cascaded

        return community_to_join

    def leave_community_with_name(self, community_name):
        self._check_can_leave_community_with_name(
            community_name=community_name)

        Community = get_community_model()
        community_to_leave = Community.objects.get(name=community_name)

        if self.has_favorite_community_with_name(community_name):
            self.unfavorite_community_with_name(community_name=community_name)

        community_to_leave.remove_member(self)

        return community_to_leave

    def invite_user_with_username_to_community_with_name(self, username, community_name):
        self._check_can_invite_user_with_username_to_community_with_name(username=username,
                                                                         community_name=community_name)

        Community = get_community_model()

        community_to_invite_user_to = Community.objects.get(name=community_name)
        user_to_invite = User.objects.get(username=username)

        community_invite = community_to_invite_user_to.create_invite(creator=self, invited_user=user_to_invite)

        self._create_community_invite_notification(community_invite)
        self._send_community_invite_push_notification(community_invite)

        return community_invite

    def uninvite_user_with_username_to_community_with_name(self, username, community_name):
        self._check_can_uninvite_user_with_username_to_community_with_name(username=username,
                                                                           community_name=community_name)

        community_invite = self.created_communities_invites.get(invited_user__username=username, creator=self,
                                                                community__name=community_name)
        uninvited_user = community_invite.invited_user
        community_invite.delete()

        return uninvited_user

    def get_community_with_name_administrators(self, community_name, max_id):
        self._check_can_get_community_with_name_administrators(
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_administrators(community_name=community_name,
                                                                administrators_max_id=max_id)

    def search_community_with_name_administrators(self, community_name, query):
        self._check_can_get_community_with_name_administrators(
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_administrators(community_name=community_name, query=query)

    def add_administrator_with_username_to_community_with_name(self, username, community_name):
        self._check_can_add_administrator_with_username_to_community_with_name(
            username=username,
            community_name=community_name)

        Community = get_community_model()

        community_to_add_administrator_to = Community.objects.get(name=community_name)
        user_to_add_as_administrator = User.objects.get(username=username)

        community_to_add_administrator_to.add_administrator(user_to_add_as_administrator)
        community_to_add_administrator_to.create_add_administrator_log(source_user=self,
                                                                       target_user=user_to_add_as_administrator)

        if user_to_add_as_administrator.is_moderator_of_community_with_name(community_name=community_name):
            self.remove_moderator_with_username_from_community_with_name(username=username,
                                                                         community_name=community_name)

        return community_to_add_administrator_to

    def remove_administrator_with_username_from_community_with_name(self, username, community_name):
        self._check_can_remove_administrator_with_username_to_community_with_name(
            username=username,
            community_name=community_name)

        Community = get_community_model()

        community_to_remove_administrator_from = Community.objects.get(name=community_name)
        user_to_remove_as_administrator = User.objects.get(username=username)

        community_to_remove_administrator_from.remove_administrator(user_to_remove_as_administrator)
        community_to_remove_administrator_from.create_remove_administrator_log(source_user=self,
                                                                               target_user=user_to_remove_as_administrator)

        return community_to_remove_administrator_from

    def get_community_with_name_moderators(self, community_name, max_id):
        self._check_can_get_community_with_name_moderators(
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_moderators(community_name=community_name,
                                                            moderators_max_id=max_id)

    def search_community_with_name_moderators(self, community_name, query):
        self._check_can_get_community_with_name_moderators(
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_moderators(community_name=community_name, query=query)

    def add_moderator_with_username_to_community_with_name(self, username, community_name):
        self._check_can_add_moderator_with_username_to_community_with_name(
            username=username,
            community_name=community_name)

        Community = get_community_model()

        community_to_add_moderator_to = Community.objects.get(name=community_name)
        user_to_add_as_moderator = User.objects.get(username=username)

        community_to_add_moderator_to.add_moderator(user_to_add_as_moderator)

        community_to_add_moderator_to.create_add_moderator_log(source_user=self,
                                                               target_user=user_to_add_as_moderator)

        return community_to_add_moderator_to

    def remove_moderator_with_username_from_community_with_name(self, username, community_name):
        self._check_can_remove_moderator_with_username_to_community_with_name(
            username=username,
            community_name=community_name)

        Community = get_community_model()

        community_to_remove_moderator_from = Community.objects.get(name=community_name)
        user_to_remove_as_moderator = User.objects.get(username=username)

        community_to_remove_moderator_from.remove_moderator(user_to_remove_as_moderator)
        community_to_remove_moderator_from.create_remove_moderator_log(source_user=self,
                                                                       target_user=user_to_remove_as_moderator)

        return community_to_remove_moderator_from

    def get_community_with_name_banned_users(self, community_name, max_id):
        self._check_can_get_community_with_name_banned_users(
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_banned_users(community_name=community_name, users_max_id=max_id)

    def search_community_with_name_banned_users(self, community_name, query):
        self._check_can_get_community_with_name_banned_users(
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_banned_users(community_name=community_name, query=query)

    def ban_user_with_username_from_community_with_name(self, username, community_name):
        self._check_can_ban_user_with_username_from_community_with_name(username=username,
                                                                        community_name=community_name)
        Community = get_community_model()

        community_to_ban_user_from = Community.objects.get(name=community_name)
        user_to_ban = User.objects.get(username=username)

        if user_to_ban.is_member_of_community_with_name(community_name=community_name):
            user_to_ban.leave_community_with_name(community_name=community_name)

        community_to_ban_user_from.banned_users.add(user_to_ban)
        community_to_ban_user_from.create_user_ban_log(source_user=self, target_user=user_to_ban)

        return community_to_ban_user_from

    def unban_user_with_username_from_community_with_name(self, username, community_name):
        self._check_can_unban_user_with_username_from_community_with_name(username=username,
                                                                          community_name=community_name)
        Community = get_community_model()

        community_to_unban_user_from = Community.objects.get(name=community_name)
        user_to_unban = User.objects.get(username=username)

        community_to_unban_user_from.banned_users.remove(user_to_unban)
        community_to_unban_user_from.create_user_unban_log(source_user=self, target_user=user_to_unban)

        return community_to_unban_user_from

    def create_list(self, name, emoji_id):
        self._check_list_name_not_taken(name)
        List = get_list_model()
        list = List.objects.create(name=name, creator=self, emoji_id=emoji_id)

        return list

    def delete_list(self, list):
        return self.delete_list_with_id(list.pk)

    def delete_list_with_id(self, list_id):
        self._check_can_delete_list_with_id(list_id)
        list = self.lists.get(id=list_id)
        list.delete()

    def update_list(self, list, **kwargs):
        return self.update_list_with_id(list.pk, **kwargs)

    def update_list_with_id(self, list_id, name=None, emoji_id=None, usernames=None):
        self._check_can_update_list_with_id(list_id)
        self._check_list_data(name, emoji_id)
        list_to_update = self.lists.get(id=list_id)

        if name:
            list_to_update.name = name

        if emoji_id:
            list_to_update.emoji_id = emoji_id

        if isinstance(usernames, list):
            # TODO This is a goddamn expensive operation. Improve.
            new_list_users = []

            list_users = list_to_update.users
            list_users_by_username = {}

            for list_user in list_users:
                list_user_username = list_user.username
                list_users_by_username[list_user_username] = list_user

            for username in usernames:
                user = User.objects.get(username=username)
                user_exists_in_list = username in list_users_by_username
                if user_exists_in_list:
                    # The username added might not be same person we had before
                    new_list_users.append(list_users_by_username[username])
                else:
                    new_list_users.append(user)

            list_users_to_remove = filter(lambda list_user: list_user not in new_list_users, list_users)

            for user_to_remove in list_users_to_remove:
                self.remove_list_with_id_from_follow_for_user_with_id(user_to_remove.pk, list_to_update.pk)

            for new_list_user in new_list_users:
                if not self.is_following_user_with_id_in_list_with_id(new_list_user.pk, list_to_update.pk):
                    if self.is_following_user_with_id(new_list_user.pk):
                        self.add_list_with_id_to_follow_for_user_with_id(new_list_user.pk, list_to_update.pk)
                    else:
                        self.follow_user_with_id(new_list_user.pk, lists_ids=[list_to_update.pk])

        list_to_update.save()
        return list_to_update

    def get_list_with_id(self, list_id):
        self._check_can_get_list_with_id(list_id)
        return self.lists.get(id=list_id)

    def search_users_with_query(self, query):
        # In the future, the user might have blocked users which should not be displayed
        return User.get_public_users_with_query(query)

    def get_linked_users(self, max_id=None):
        # All users which are connected with us and we have accepted by adding
        # them to a circle
        linked_users_query = self._make_linked_users_query(max_id=max_id)

        return User.objects.filter(linked_users_query).distinct()

    def search_linked_users_with_query(self, query):
        linked_users_query = self._make_linked_users_query()

        names_query = Q(username__icontains=query)
        names_query.add(Q(profile__name__icontains=query), Q.OR)

        linked_users_query.add(names_query, Q.AND)

        return User.objects.filter(linked_users_query).distinct()

    def search_communities_with_query(self, query):
        # In the future, the user might have blocked communities which should not be displayed
        Community = get_community_model()
        return Community.search_communities_with_query(query)

    def get_community_with_name(self, community_name):
        Community = get_community_model()
        return Community.objects.get(name=community_name)

    def get_joined_communities(self):
        Community = get_community_model()
        return Community.objects.filter(memberships__user=self)

    def search_joined_communities_with_query(self, query):
        joined_communities_query = Q(memberships__user=self)
        joined_communities_name_query = Q(name__icontains=query)
        joined_communities_name_query.add(Q(title__icontains=query), Q.OR)
        joined_communities_query.add(joined_communities_name_query, Q.AND)
        Community = get_community_model()
        return Community.objects.filter(joined_communities_query)

    def get_favorite_communities(self):
        return self.favorite_communities.all()

    def get_administrated_communities(self):
        Community = get_community_model()
        return Community.objects.filter(memberships__user=self, memberships__is_administrator=True)

    def get_moderated_communities(self):
        Community = get_community_model()
        return Community.objects.filter(memberships__user=self, memberships__is_moderator=True)

    def create_public_post(self, text=None, image=None, video=None, created=None):
        world_circle_id = self._get_world_circle_id()
        return self.create_encircled_post(text=text, image=image, video=video, circles_ids=[world_circle_id],
                                          created=created)

    def create_encircled_post(self, circles_ids, text=None, image=None, video=None, created=None):
        self._check_can_post_to_circles_with_ids(circles_ids=circles_ids)
        Post = get_post_model()
        post = Post.create_post(text=text, creator=self, circles_ids=circles_ids, image=image, video=video,
                                created=created)
        return post

    def update_post(self, post_id, text=None):
        self._check_can_update_post_with_id(post_id)
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        post.update(text=text)
        return post

    def create_community_post(self, community_name, text=None, image=None, video=None, created=None):
        self._check_can_post_to_community_with_name(community_name=community_name)
        Post = get_post_model()
        post = Post.create_post(text=text, creator=self, community_name=community_name, image=image, video=video,
                                created=created)

        return post

    def delete_post(self, post):
        return self.delete_post_with_id(post.pk)

    def delete_post_with_id(self, post_id):
        self._check_can_delete_post_with_id(post_id)
        Post = get_post_model()

        # We have to manually delete the images / video
        post = Post.objects.get(id=post_id)

        if post.has_video():
            delete_file_field(post.video.video)

        if post.has_image():
            delete_file_field(post.image.image)

        # We have to be mindful with using bulk delete as it does not call the delete() method per instance
        Post.objects.filter(id=post_id).delete()

    def get_posts_for_community_with_name(self, community_name, max_id=None):
        """
        :param community_name:
        :param max_id:
        :return:
        """
        self._check_can_get_posts_for_community_with_name(community_name=community_name)

        Community = get_community_model()
        community = Community.objects.get(name=community_name)

        posts_query = Q(community__id=community.pk)

        if max_id:
            posts_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()
        profile_posts = Post.objects.filter(posts_query).distinct()

        return profile_posts

    def get_post_with_id(self, post_id):
        self._check_can_see_post_with_id(post_id=post_id)
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        return post

    def get_community_post_with_id(self, post_id):
        Community = get_community_model()
        post_query = Q(id=post_id)

        post_query_visibility_query = Q(community__memberships__user__id=self.pk)
        post_query_visibility_query.add(Q(community__type=Community.COMMUNITY_TYPE_PUBLIC, ), Q.OR)

        post_query.add(post_query_visibility_query, Q.AND)

        Post = get_post_model()
        profile_posts = Post.objects.filter(post_query)

        return profile_posts

    def get_posts(self, max_id=None):
        """
        Get all the posts for ourselves
        :param max_id:
        :return:
        """
        posts_query = Q(creator_id=self.id, community__isnull=True)

        if max_id:
            posts_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()
        posts = Post.objects.filter(posts_query)

        return posts

    def get_posts_for_user_with_username(self, username, max_id=None):
        """
        Get all the posts for the given user with username
        :param username:
        :param max_id:
        :param post_id:
        :return:
        """
        user = User.objects.get(username=username)
        posts_query = self._make_get_posts_query_for_user(user, max_id)

        Post = get_post_model()
        profile_posts = Post.objects.filter(posts_query).distinct()

        return profile_posts

    def get_timeline_posts(self, lists_ids=None, circles_ids=None, max_id=None):
        """
        Get the timeline posts for self. The results will be dynamic based on follows and connections.
        """

        if not circles_ids and not lists_ids:
            return self._get_timeline_posts_with_no_filters(max_id=max_id)

        return self._get_timeline_posts_with_filters(max_id=max_id, circles_ids=circles_ids, lists_ids=lists_ids)

    def _get_timeline_posts_with_filters(self, max_id=None, circles_ids=None, lists_ids=None):
        world_circle_id = self._get_world_circle_id()

        if circles_ids:
            timeline_posts_query = Q(creator=self.pk, circles__id__in=circles_ids)
        else:
            timeline_posts_query = Q()

        if lists_ids:
            followed_users_query = self.follows.filter(lists__id__in=lists_ids)
        else:
            followed_users_query = self.follows.all()

        followed_users = followed_users_query.values('followed_user__id')

        for followed_user in followed_users:

            followed_user_id = followed_user['followed_user__id']

            followed_user_query = Q(creator_id=followed_user_id)

            if circles_ids:
                followed_user_query.add(Q(creator__connections__target_connection__circles__in=circles_ids), Q.AND)

            followed_user_circles_query = Q(circles__id=world_circle_id)

            followed_user_circles_query.add(Q(circles__connections__target_user_id=self.pk,
                                              circles__connections__target_connection__circles__isnull=False), Q.OR)

            followed_user_query.add(followed_user_circles_query, Q.AND)

            # Add all followed user circles
            timeline_posts_query.add(followed_user_query, Q.OR)

        if max_id:
            timeline_posts_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()
        return Post.objects.filter(timeline_posts_query).distinct()

    def _get_timeline_posts_with_no_filters(self, max_id=None):
        """
        Being the main action of the network, an optimised call of the get timeline posts call with no filtering.
        """
        world_circle_id = self._get_world_circle_id()

        # Add all own posts
        timeline_posts_query = Q(creator=self.pk)

        # Add all community posts
        timeline_posts_query.add(Q(community__memberships__user__id=self.pk), Q.OR)

        timeline_posts_query.add(Q(circles__connections__target_user_id=self.pk,
                                   circles__connections__target_connection__circles__isnull=False), Q.OR)

        followed_users = self.follows.values('followed_user_id').cache()

        followed_users_ids = [followed_user['followed_user_id'] for followed_user in followed_users]

        timeline_posts_query.add(Q(creator__in=followed_users_ids, circles__id=world_circle_id), Q.OR)

        if max_id:
            timeline_posts_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()

        return Post.objects.filter(timeline_posts_query).distinct()

    def follow_user(self, user, lists_ids=None):
        return self.follow_user_with_id(user.pk, lists_ids)

    def follow_user_with_id(self, user_id, lists_ids=None):
        self._check_can_follow_user_with_id(user_id=user_id)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot follow itself.'),
            )

        if not lists_ids:
            lists_ids = self._get_default_follow_lists()

        self._check_follow_lists_ids(lists_ids)

        Follow = get_follow_model()
        follow = Follow.create_follow(user_id=self.pk, followed_user_id=user_id, lists_ids=lists_ids)
        self._create_follow_notification(followed_user_id=user_id)
        self._send_follow_push_notification(followed_user_id=user_id)

        return follow

    def unfollow_user(self, user):
        return self.unfollow_user_with_id(user.pk)

    def unfollow_user_with_id(self, user_id):
        self._check_is_following_user_with_id(user_id)
        follow = self.follows.get(followed_user_id=user_id)
        self._delete_follow_notification(followed_user_id=user_id)
        follow.delete()

    def update_follow_for_user(self, user, lists_ids=None):
        return self.update_follow_for_user_with_id(user.pk, lists_ids=lists_ids)

    def update_follow_for_user_with_id(self, user_id, lists_ids=None):
        self._check_is_following_user_with_id(user_id)

        if not lists_ids:
            lists_ids = self._get_default_follow_lists()

        self._check_follow_lists_ids(lists_ids)

        follow = self.get_follow_for_user_with_id(user_id)

        follow.lists.clear()
        follow.lists.add(*lists_ids)
        follow.save()

        return follow

    def remove_list_with_id_from_follow_for_user_with_id(self, user_id, list_id):
        self._check_is_following_user_with_id(user_id)
        self._check_is_following_user_with_id_in_list_with_id(user_id, list_id)
        follow = self.get_follow_for_user_with_id(user_id)
        follow.lists.remove(list_id)
        return follow

    def add_list_with_id_to_follow_for_user_with_id(self, user_id, list_id):
        self._check_is_following_user_with_id(user_id)
        self._check_is_not_following_user_with_id_in_list_with_id(user_id, list_id)
        follow = self.get_follow_for_user_with_id(user_id)
        follow.lists.add(list_id)
        return follow

    def connect_with_user_with_id(self, user_id, circles_ids=None):
        self._check_is_not_connected_with_user_with_id(user_id)

        if not circles_ids:
            circles_ids = self._get_default_connection_circles()
        elif self.connections_circle_id not in circles_ids:
            circles_ids.append(self.connections_circle_id)

        self._check_connection_circles_ids(circles_ids)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot connect with itself.'),
            )

        Connection = get_connection_model()
        connection = Connection.create_connection(user_id=self.pk, target_user_id=user_id, circles_ids=circles_ids)

        # Automatically follow user
        if not self.is_following_user_with_id(user_id):
            self.follow_user_with_id(user_id)

        self._create_connection_request_notification(user_connection_requested_for_id=user_id)
        self._send_connection_request_push_notification(user_connection_requested_for_id=user_id)

        return connection

    def confirm_connection_with_user_with_id(self, user_id, circles_ids=None):
        self._check_is_not_fully_connected_with_user_with_id(user_id)

        if not circles_ids:
            circles_ids = self._get_default_connection_circles()
        elif self.connections_circle_id not in circles_ids:
            circles_ids.append(self.connections_circle_id)

        self._check_connection_circles_ids(circles_ids)
        connection = self.update_connection_with_user_with_id(user_id, circles_ids=circles_ids)

        # Automatically follow user
        if not self.is_following_user_with_id(user_id):
            self.follow_user_with_id(user_id)

        self._create_connection_confirmed_notification(user_connected_with_id=user_id)

        return connection

    def update_connection_with_user_with_id(self, user_id, circles_ids=None):
        self._check_is_connected_with_user_with_id(user_id)

        if not circles_ids:
            raise ValidationError(
                _('No data to update the connection with.'),
            )
        elif self.connections_circle_id not in circles_ids:
            circles_ids.append(self.connections_circle_id)

        self._check_connection_circles_ids(circles_ids)

        connection = self.get_connection_for_user_with_id(user_id)
        connection.circles.clear()
        connection.circles.add(*circles_ids)
        connection.save()

        return connection

    def disconnect_from_user(self, user):
        return self.disconnect_from_user_with_id(user.pk)

    def disconnect_from_user_with_id(self, user_id):
        self._check_is_connected_with_user_with_id(user_id)
        if self.is_fully_connected_with_user_with_id(user_id):
            self._delete_connection_confirmed_notification(user_connected_with_id=user_id)
            if self.is_following_user_with_id(user_id):
                self.unfollow_user_with_id(user_id)
        else:
            self._delete_connection_request_notification_for_user_with_id(user_id=user_id)

        connection = self.connections.get(target_connection__user_id=user_id)
        connection.delete()

        return connection

    def get_connection_for_user_with_id(self, user_id):
        return self.connections.get(target_connection__user_id=user_id)

    def get_follow_for_user_with_id(self, user_id):
        return self.follows.get(followed_user_id=user_id)

    def get_notifications(self, max_id=None):
        notifications_query = Q()

        if max_id:
            notifications_query.add(Q(id__lt=max_id), Q.AND)

        return self.notifications.filter(notifications_query)

    def read_notifications(self, max_id=None):
        notifications_query = Q(read=False)

        if max_id:
            notifications_query.add(Q(id__lte=max_id), Q.AND)

        self.notifications.filter(notifications_query).update(read=True)

    def read_notification_with_id(self, notification_id):
        self._check_can_read_notification_with_id(notification_id)
        notification = self.notifications.get(id=notification_id)
        notification.read = True
        notification.save()
        return notification

    def delete_notification_with_id(self, notification_id):
        self._check_can_delete_notification_with_id(notification_id)
        notification = self.notifications.get(id=notification_id)
        notification.delete()

    def delete_notifications(self):
        self.notifications.all().delete()

    def create_device(self, uuid, name=None):
        self._check_device_with_uuid_does_not_exist(uuid)
        Device = get_device_model()
        return Device.create_device(owner=self, uuid=uuid, name=name)

    def update_device_with_uuid(self, device_uuid, name=None):
        self._check_can_update_device_with_uuid(device_uuid=device_uuid)
        device = self.devices.get(uuid=device_uuid)
        device.update(name=name)

    def delete_device_with_uuid(self, device_uuid):
        self._check_can_delete_device_with_uuid(device_uuid=device_uuid)
        device = self.devices.get(uuid=device_uuid)
        device.delete()

    def get_devices(self, max_id=None):
        devices_query = Q()

        if max_id:
            devices_query.add(Q(id__lt=max_id), Q.AND)

        return self.devices.filter(devices_query)

    def get_device_with_uuid(self, device_uuid):
        self._check_can_get_device_with_uuid(device_uuid=device_uuid)
        return self.devices.get(uuid=device_uuid)

    def delete_devices(self):
        self.devices.all().delete()

    def mute_post_with_id(self, post_id):
        self._check_can_mute_post_with_id(post_id=post_id)
        Post = get_post_model()
        PostMute = get_post_mute_model()
        PostMute.create_post_mute(post_id=post_id, muter_id=self.pk)
        post = Post.objects.get(pk=post_id)
        return post

    def unmute_post_with_id(self, post_id):
        self._check_can_unmute_post_with_id(post_id=post_id)
        self.post_mutes.filter(post_id=post_id).delete()
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        return post

    def _generate_password_reset_link(self, token):
        return '{0}/api/auth/password/verify?token={1}'.format(settings.EMAIL_HOST, token)

    def _send_password_reset_email_with_token(self, password_reset_token):
        mail_subject = _('Reset your password for Openbook')
        text_content = render_to_string('openbook_auth/email/reset_password.txt', {
            'name': self.profile.name,
            'username': self.username,
            'password_reset_link': self._generate_password_reset_link(password_reset_token)
        })

        html_content = render_to_string('openbook_auth/email/reset_password.html', {
            'name': self.profile.name,
            'username': self.username,
            'password_reset_link': self._generate_password_reset_link(password_reset_token)
        })

        email = EmailMultiAlternatives(
            mail_subject, text_content, to=[self.email], from_email=settings.SERVICE_EMAIL_ADDRESS)
        email.attach_alternative(html_content, 'text/html')
        email.send()

    def _send_post_comment_push_notification(self, post_comment, notification_message, notification_target_user):
        senders.send_post_comment_push_notification_with_message(post_comment=post_comment,
                                                                 message=notification_message,
                                                                 target_user=notification_target_user)

    def _delete_post_comment_notification(self, post_comment):
        PostCommentNotification = get_post_comment_notification_model()
        PostCommentNotification.delete_post_comment_notification(post_comment_id=post_comment.pk,
                                                                 owner_id=post_comment.post.creator_id)

    def _create_post_reaction_notification(self, post_reaction):
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.create_post_reaction_notification(post_reaction_id=post_reaction.pk,
                                                                   owner_id=post_reaction.post.creator_id)

    def _send_post_reaction_push_notification(self, post_reaction):
        senders.send_post_reaction_push_notification(post_reaction=post_reaction)

    def _delete_post_reaction_notification(self, post_reaction):
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.delete_post_reaction_notification(post_reaction_id=post_reaction.pk,
                                                                   owner_id=post_reaction.post.creator_id)

    def _create_community_invite_notification(self, community_invite):
        CommunityInviteNotification = get_community_invite_notification_model()
        CommunityInviteNotification.create_community_invite_notification(community_invite_id=community_invite.pk,
                                                                         owner_id=community_invite.invited_user_id)

    def _send_community_invite_push_notification(self, community_invite):
        senders.send_community_invite_push_notification(community_invite=community_invite)

    def _create_follow_notification(self, followed_user_id):
        FollowNotification = get_follow_notification_model()
        FollowNotification.create_follow_notification(follower_id=self.pk, owner_id=followed_user_id)

    def _send_follow_push_notification(self, followed_user_id):
        followed_user = User.objects.get(pk=followed_user_id)
        senders.send_follow_push_notification(followed_user=followed_user, following_user=self)

    def _delete_follow_notification(self, followed_user_id):
        FollowNotification = get_follow_notification_model()
        FollowNotification.delete_follow_notification(follower_id=self.pk, owner_id=followed_user_id)

    def _create_connection_confirmed_notification(self, user_connected_with_id):
        # Remove the connection request we got from the other user
        self._delete_connection_request_notification_for_user_with_id(user_id=user_connected_with_id)
        ConnectionConfirmedNotification = get_connection_confirmed_notification_model()
        ConnectionConfirmedNotification.create_connection_confirmed_notification(connection_confirmator_id=self.pk,
                                                                                 owner_id=user_connected_with_id)

    def _delete_connection_confirmed_notification(self, user_connected_with_id):
        ConnectionConfirmedNotification = get_connection_confirmed_notification_model()
        ConnectionConfirmedNotification.delete_connection_confirmed_notification_for_users_with_ids(
            user_a_id=self.pk,
            user_b_id=user_connected_with_id)

    def _create_connection_request_notification(self, user_connection_requested_for_id):
        ConnectionRequestNotification = get_connection_request_notification_model()
        ConnectionRequestNotification.create_connection_request_notification(connection_requester_id=self.pk,
                                                                             owner_id=user_connection_requested_for_id)

    def _send_connection_request_push_notification(self, user_connection_requested_for_id):
        connection_requested_for = User.objects.get(pk=user_connection_requested_for_id)
        senders.send_connection_request_push_notification(
            connection_requester=self,
            connection_requested_for=connection_requested_for)

    def _delete_connection_request_notification_for_user_with_id(self, user_id):
        ConnectionRequestNotification = get_connection_request_notification_model()
        ConnectionRequestNotification.delete_connection_request_notification_for_users_with_ids(user_a_id=self.pk,
                                                                                                user_b_id=user_id)

    def _make_linked_users_query(self, max_id=None):
        # All users which are connected with us and we have accepted by adding
        # them to a circle
        linked_users_query = Q(circles__connections__target_connection__user_id=self.pk,
                               circles__connections__target_connection__circles__isnull=False)

        # All users following us
        linked_users_query.add(Q(follows__followed_user_id=self.pk), Q.OR)

        if max_id:
            linked_users_query.add(Q(id__lt=max_id), Q.AND)

        return linked_users_query

    def _make_get_post_with_id_query_for_user(self, user, post_id):
        posts_query = self._make_get_posts_query_for_user(user)
        posts_query.add(Q(id=post_id), Q.AND)
        return posts_query

    def _make_get_posts_query_for_user(self, user, max_id=None):
        posts_query = Q()

        # Add the user world circle posts
        world_circle_id = self._get_world_circle_id()
        user_world_circle_posts_query = Q(creator_id=user.pk,
                                          circles__id=world_circle_id)
        posts_query.add(user_world_circle_posts_query, Q.OR)

        is_fully_connected_with_user = self.is_fully_connected_with_user_with_id(user.pk)

        if is_fully_connected_with_user:
            # Add the user connections circle posts
            user_connections_circle_query = Q(creator_id=user.pk,
                                              circles__id=user.connections_circle_id)

            posts_query.add(user_connections_circle_query, Q.OR)

            # Add the user circled posts we're part of
            Connection = get_connection_model()

            connection = Connection.objects.prefetch_related(
                'target_connection__circles'
            ).filter(
                user_id=self.pk,
                target_connection__user_id=user.pk).get()

            target_connection_circles = connection.target_connection.circles.all()

            if target_connection_circles:
                target_connection_circles_ids = [target_connection_circle.pk for target_connection_circle in
                                                 target_connection_circles]

                user_encircled_posts_query = Q(creator_id=user.pk, circles__id__in=target_connection_circles_ids)
                posts_query.add(user_encircled_posts_query, Q.OR)

        if max_id:
            posts_query.add(Q(id__lt=max_id), Q.AND)

        return posts_query

    def _get_world_circle_id(self):
        Circle = get_circle_model()
        return Circle.get_world_circle().pk

    def _get_default_connection_circles(self):
        """
        If no circles were given on a connection request or confirm,
        these will be the ones used.
        :return:
        """
        return [self.connections_circle_id]

    def _get_default_follow_lists(self):
        """
        If no list were given on follow,
        these will be the ones used.
        :return:
        """
        return []

    def _make_email_verification_token_for_email(self, new_email):
        return jwt.encode({'type': self.JWT_TOKEN_TYPE_CHANGE_EMAIL,
                           'new_email': new_email,
                           'email': self.email,
                           'user_id': self.pk,
                           'exp': datetime.utcnow() + timedelta(days=1)},
                          settings.SECRET_KEY,
                          algorithm=settings.JWT_ALGORITHM).decode('utf-8')

    def _make_password_reset_verification_token(self):
        return jwt.encode({'type': self.JWT_TOKEN_TYPE_PASSWORD_RESET,
                           'user_id': self.pk,
                           'exp': datetime.utcnow() + timedelta(days=1)},
                          settings.SECRET_KEY,
                          algorithm=settings.JWT_ALGORITHM).decode('utf-8')

    def _check_password_reset_verification_token_is_valid(self, password_verification_token):
        try:
            token_contents = jwt.decode(password_verification_token, settings.SECRET_KEY,
                                        algorithm=settings.JWT_ALGORITHM)

            token_user_id = token_contents['user_id']
            token_type = token_contents['type']

            if token_type != self.JWT_TOKEN_TYPE_PASSWORD_RESET:
                raise ValidationError(
                    _('Token type does not match')
                )

            if token_user_id != self.pk:
                raise ValidationError(
                    _('Token user id does not match')
                )
            return token_user_id
        except jwt.InvalidSignatureError:
            raise ValidationError(
                _('Invalid token signature')
            )
        except jwt.ExpiredSignatureError:
            raise ValidationError(
                _('Token expired')
            )
        except jwt.DecodeError:
            raise ValidationError(
                _('Failed to decode token')
            )
        except KeyError:
            raise ValidationError(
                _('Invalid token')
            )

    def _check_email_verification_token_is_valid_for_email(self, email_verification_token):
        try:
            token_contents = jwt.decode(email_verification_token, settings.SECRET_KEY,
                                        algorithm=settings.JWT_ALGORITHM)
            token_email = token_contents['email']
            new_email = token_contents['new_email']
            token_user_id = token_contents['user_id']
            token_type = token_contents['type']

            if token_type != self.JWT_TOKEN_TYPE_CHANGE_EMAIL:
                raise ValidationError(
                    _('Token type does not match')
                )

            if token_email != self.email:
                raise ValidationError(
                    _('Token email does not match')
                )

            if token_user_id != self.pk:
                raise ValidationError(
                    _('Token user id does not match')
                )
            return new_email
        except jwt.InvalidSignatureError:
            raise ValidationError(
                _('Invalid token signature')
            )
        except jwt.ExpiredSignatureError:
            raise ValidationError(
                _('Token expired')
            )
        except jwt.DecodeError:
            raise ValidationError(
                _('Failed to decode token')
            )
        except KeyError:
            raise ValidationError(
                _('Invalid token')
            )

    def _check_connection_circles_ids(self, circles_ids):
        for circle_id in circles_ids:
            self._check_connection_circle_id(circle_id)

    def _check_connection_circle_id(self, circle_id):
        self._check_has_circle_with_id(circle_id)

        if self.is_world_circle_id(circle_id):
            raise ValidationError(
                _('Can\'t connect in the world circle.'),
            )

    def _check_email_not_taken(self, email):
        if email == self.email:
            return

        if User.is_email_taken(email=email):
            raise ValidationError(
                _('The email is already taken.')
            )

    def _check_username_not_taken(self, username):
        if username == self.username:
            return

        if User.is_username_taken(username=username):
            raise ValidationError(
                _('The username is already taken.')
            )

    def _check_can_edit_comment_with_id_for_post_with_id(self, post_comment_id, post_id):
        # Check that the comment belongs to the post
        PostComment = get_post_comment_model()
        Post = get_post_model()

        if not PostComment.objects.filter(id=post_comment_id, post_id=post_id).exists():
            raise ValidationError(
                _('The comment does not belong to the specified post.')
            )

    def _check_has_post_comment_with_id(self, post_comment_id):
        if not self.posts_comments.filter(id=post_comment_id).exists():
            # The comment is not ours
            raise ValidationError(
                _('You cannot edit a comment that does not belong to you')
            )

    def _check_can_delete_comment_with_id_for_post_with_id(self, post_comment_id, post_id):

        # Check that the comment belongs to the post
        PostComment = get_post_comment_model()
        Post = get_post_model()

        if not PostComment.objects.filter(id=post_comment_id, post_id=post_id).exists():
            raise ValidationError(
                _('The comment does not belong to the specified post.')
            )

        if not self.has_post_with_id(post_id):
            if not self.posts_comments.filter(id=post_comment_id).exists():
                # The comment is not ours
                if Post.is_post_with_id_a_community_post(post_id):
                    # If the comment is in a community, check if we're moderators
                    post = Post.objects.select_related('community').get(pk=post_id)
                    if not self.is_moderator_of_community_with_name(
                            post.community.name) and not self.is_administrator_of_community_with_name(
                        post.community.name):
                        raise ValidationError(
                            _('Only moderators/administrators can remove community posts.'),
                        )
                    else:
                        post_comment = PostComment.objects.select_related('commenter').get(pk=post_comment_id)
                        post.community.create_remove_post_comment_log(source_user=self,
                                                                      target_user=post_comment.commenter)
                else:
                    raise ValidationError(
                        _('You cannot remove a comment that does not belong to you')
                    )

    def _check_can_get_comments_for_post_with_id(self, post_id):
        self._check_can_see_post_with_id(post_id)

    def _check_can_comment_in_post_with_id(self, post_id):
        self._check_can_see_post_with_id(post_id)

    def _check_can_delete_reaction_with_id_for_post_with_id(self, post_reaction_id, post_id):
        # Check if the post belongs to us
        if self.has_post_with_id(post_id):
            # Check that the comment belongs to the post
            PostReaction = get_post_reaction_model()
            if PostReaction.objects.filter(id=post_reaction_id, post_id=post_id).count() == 0:
                raise ValidationError(
                    _('That reaction does not belong to the specified post.')
                )
            return

        if self.post_reactions.filter(id=post_reaction_id).count() == 0:
            raise ValidationError(
                _('Can\'t delete a reaction that does not belong to you.'),
            )

    def _check_can_get_reactions_for_post_with_id(self, post_id):
        self._check_can_see_post_with_id(post_id)

    def _check_can_react_with_emoji_id_and_emoji_group_id(self, emoji_id, emoji_group_id):
        EmojiGroup = get_emoji_group_model()
        try:
            emoji_group = EmojiGroup.objects.get(pk=emoji_group_id, is_reaction_group=True)
            if not emoji_group.has_emoji_with_id(emoji_id):
                raise ValidationError(
                    _('Emoji does not belong to given emoji group.'),
                )
        except EmojiGroup.DoesNotExist:
            raise ValidationError(
                _('Emoji group does not exist or is not a reaction group.'),
            )

    def _check_can_react_to_post_with_id(self, post_id):
        self._check_can_see_post_with_id(post_id)

    def _check_can_see_post_with_id(self, post_id):
        # Check if post is public
        Post = get_post_model()
        post = Post.objects.select_related('creator').filter(pk=post_id).get()
        if post.creator_id == self.pk or post.is_public_post():
            return

        if post.community:
            if not self.get_community_post_with_id(post_id=post_id).exists():
                raise ValidationError(
                    _('This post is from a private community.'),
                )
        else:
            # Check if we can retrieve the post
            if not self._can_see_post(post=post):
                raise ValidationError(
                    _('This post is private.'),
                )

    def _can_see_post(self, post):
        post_query = self._make_get_post_with_id_query_for_user(post.creator, post_id=post.pk)

        Post = get_post_model()
        profile_posts = Post.objects.filter(post_query)

        return profile_posts.exists()

    def _check_follow_lists_ids(self, lists_ids):
        for list_id in lists_ids:
            self._check_follow_list_id(list_id)

    def _check_follow_list_id(self, list_id):
        self._check_has_list_with_id(list_id)

    def _check_can_update_post_with_id(self, post_id):
        self._check_has_post_with_id(post_id=post_id)

    def _check_can_post_to_circles_with_ids(self, circles_ids=None):
        for circle_id in circles_ids:
            if not self.has_circle_with_id(circle_id) and not self.is_world_circle_id(circle_id):
                raise ValidationError(
                    _('You cannot post to circle with id %(id)s') % {'id': circle_id},
                )

    def _check_can_post_to_community_with_name(self, community_name=None):
        if not self.is_member_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You cannot post to a community you\'re not member of '),
            )

    def _check_list_data(self, name, emoji_id):
        if name:
            self._check_list_name_not_taken(name)

    def _check_community_data(self, name=None, avatar=None, cover=None):
        if name:
            self._check_community_name_not_taken(name)

    def _check_circle_data(self, name, color):
        if name:
            self._check_circle_name_not_taken(name)

    def _check_can_follow_user_with_id(self, user_id):
        self._check_is_not_following_user_with_id(user_id)
        self._check_has_not_reached_max_follows()

    def _check_is_not_following_user_with_id(self, user_id):
        if self.is_following_user_with_id(user_id):
            raise ValidationError(
                _('Already following user.'),
            )

    def _check_has_not_reached_max_follows(self):
        if self.count_following() > settings.USER_MAX_FOLLOWS:
            raise ValidationError(
                _('Maximum number of follows reached.'),
            )

    def _check_is_not_following_user_with_id_in_list_with_id(self, user_id, list_id):
        self._check_is_following_user_with_id(user_id)

        if self.is_following_user_with_id_in_list_with_id(user_id, list_id):
            raise ValidationError(
                _('Already following user in list.'),
            )

    def _check_is_following_user_with_id_in_list_with_id(self, user_id, list_id):
        self._check_is_following_user_with_id(user_id)

        if not self.is_following_user_with_id_in_list_with_id(user_id, list_id):
            raise ValidationError(
                _('Not following user in list.'),
            )

    def _check_is_following_user_with_id(self, user_id):
        if not self.is_following_user_with_id(user_id):
            raise ValidationError(
                _('Not following user.'),
            )

    def _check_can_connect_with_user_with_id(self, user_id):
        self._check_is_not_connected_with_user_with_id(user_id)
        self._check_has_not_reached_max_connections()

    def _check_has_not_reached_max_connections(self):
        if self.count_connections() > settings.USER_MAX_CONNECTIONS:
            raise ValidationError(
                _('Maximum number of connections reached.'),
            )

    def _check_is_not_connected_with_user_with_id(self, user_id):
        if self.is_connected_with_user_with_id(user_id):
            raise ValidationError(
                _('Already connected with user.'),
            )

    def _check_is_not_fully_connected_with_user_with_id(self, user_id):
        if self.is_fully_connected_with_user_with_id(user_id):
            raise ValidationError(
                _('Already fully connected with user.'),
            )

    def _check_is_connected_with_user_with_id(self, user_id):
        if not self.is_connected_with_user_with_id(user_id):
            raise ValidationError(
                _('Not connected with user.'),
            )

    def _check_is_connected_with_user_with_id_in_circle_with_id(self, user_id, circle_id):
        if not self.is_connected_with_user_with_id_in_circle_with_id(user_id, circle_id):
            raise ValidationError(
                _('Not connected with user in given circle.'),
            )

    def _check_is_not_connected_with_user_with_id_in_circle_with_id(self, user_id, circle_id):
        if self.is_connected_with_user_with_id_in_circle_with_id(user_id, circle_id):
            raise ValidationError(
                _('Already connected with user in given circle.'),
            )

    def _check_has_list_with_id(self, list_id):
        if not self.has_list_with_id(list_id):
            raise ValidationError(
                _('List does not exist.'),
            )

    def _check_has_circle_with_id(self, circle_id):
        if not self.has_circle_with_id(circle_id):
            raise ValidationError(
                _('Circle does not exist.'),
            )

    def _check_has_circles_with_ids(self, circles_ids):
        if not self.has_circles_with_ids(circles_ids):
            raise ValidationError(
                _('One or more of the circles do not exist.'),
            )

    def _check_can_delete_post_with_id(self, post_id):
        Post = get_post_model()

        if not self.has_post_with_id(post_id):
            if Post.is_post_with_id_a_community_post(post_id):
                # If the comment is in a community, check if we're moderators
                post = Post.objects.select_related('community').get(pk=post_id)
                if not self.is_moderator_of_community_with_name(
                        post.community.name) and not self.is_administrator_of_community_with_name(post.community.name):
                    raise ValidationError(
                        _('Only moderators/administrators can remove community posts.'),
                    )
                else:
                    # TODO Not the best place to log this but doing the check for community again on delete is wasteful
                    post.community.create_remove_post_log(source_user=self,
                                                          target_user=post.creator)
            else:
                raise ValidationError(
                    _('You cannot remove a post that does not belong to you')
                )

    def _check_can_delete_list_with_id(self, list_id):
        if not self.has_list_with_id(list_id):
            raise ValidationError(
                _('Can\'t delete a list that does not belong to you.'),
            )

    def _check_can_update_list_with_id(self, list_id):
        if not self.has_list_with_id(list_id):
            raise ValidationError(
                _('Can\'t update a list that does not belong to you.'),
            )

    def _check_can_delete_community_with_name(self, community_name):
        if not self.is_creator_of_community_with_name(community_name):
            raise ValidationError(
                _('Can\'t delete a community that you do not administrate.'),
            )

    def _check_can_update_community_with_name(self, community_name):
        if not self.is_administrator_of_community_with_name(community_name):
            raise ValidationError(
                _('Can\'t update a community that you do not administrate.'),
            )

    def _check_can_get_posts_for_community_with_name(self, community_name):
        Community = get_community_model()
        if Community.is_community_with_name_private(
                community_name=community_name) and not self.is_member_of_community_with_name(
            community_name=community_name):
            raise ValidationError(
                _('The community is private. You must become a member to retrieve its posts.'),
            )

    def _check_can_get_community_with_name_members(self, community_name):
        if self.is_banned_from_community_with_name(community_name):
            raise ValidationError('You can\'t get the members of a community you have been banned from.')

        Community = get_community_model()

        if Community.is_community_with_name_private(community_name=community_name):
            if not self.is_member_of_community_with_name(community_name=community_name):
                raise ValidationError(
                    _('Can\'t see the members of a private community.'),
                )

    def _check_can_join_community_with_name(self, community_name):
        if self.is_banned_from_community_with_name(community_name):
            raise ValidationError('You can\'t join a community you have been banned from.')

        if self.is_member_of_community_with_name(community_name):
            raise ValidationError(
                _('You are already a member of the community.'),
            )

        Community = get_community_model()
        if Community.is_community_with_name_private(community_name=community_name):
            if not self.is_invited_to_community_with_name(community_name=community_name):
                raise ValidationError(
                    _('You are not invited to join this community.'),
                )

    def _check_can_leave_community_with_name(self, community_name):
        if not self.is_member_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You cannot leave a community you\'re not part of.'),
            )

        if self.is_creator_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You cannot leave a community you created.'),
            )

    def _check_can_invite_user_with_username_to_community_with_name(self, username, community_name):
        if not self.is_member_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You can only invite people to a community you are member of.'),
            )

        if self.has_invited_user_with_username_to_community_with_name(username=username, community_name=community_name):
            raise ValidationError(
                _('You have already invited this user to join the community.'),
            )

        Community = get_community_model()

        if Community.is_user_with_username_member_of_community_with_name(username=username,
                                                                         community_name=community_name):
            raise ValidationError(
                _('The user is already part of the community.'),
            )

        if not Community.is_community_with_name_invites_enabled(community_name=community_name) and not (
                self.is_administrator_of_community_with_name(
                    community_name=community_name) or self.is_moderator_of_community_with_name(
            community_name=community_name)):
            raise ValidationError(
                _('Invites for this community are not enabled. Only administrators & moderators can invite.'),
            )

    def _check_can_uninvite_user_with_username_to_community_with_name(self, username, community_name):
        if not self.has_invited_user_with_username_to_community_with_name(username=username,
                                                                          community_name=community_name):
            raise ValidationError(
                _('No invite to withdraw.'),
            )

    def _check_can_get_community_with_name_banned_users(self, community_name):
        if not self.is_administrator_of_community_with_name(
                community_name=community_name) and not self.is_moderator_of_community_with_name(
            community_name=community_name):
            raise ValidationError(
                _('Only community administrators & moderators can get banned users.'),
            )

    def _check_can_ban_user_with_username_from_community_with_name(self, username, community_name):
        if not self.is_administrator_of_community_with_name(
                community_name=community_name) and not self.is_moderator_of_community_with_name(
            community_name=community_name):
            raise ValidationError(
                _('Only community administrators & moderators can ban community members.'),
            )

        Community = get_community_model()
        if Community.is_user_with_username_banned_from_community_with_name(username=username,
                                                                           community_name=community_name):
            raise ValidationError(
                _('User is already banned'),
            )

        if Community.is_user_with_username_moderator_of_community_with_name(username=username,
                                                                            community_name=community_name) or Community.is_user_with_username_administrator_of_community_with_name(
            username=username, community_name=community_name):
            raise ValidationError(
                _('You can\'t ban moderators or administrators of the community'),
            )

    def _check_can_unban_user_with_username_from_community_with_name(self, username, community_name):
        if not self.is_administrator_of_community_with_name(
                community_name=community_name) and not self.is_moderator_of_community_with_name(
            community_name=community_name):
            raise ValidationError(
                _('Only community administrators & moderators can ban community members.'),
            )

        Community = get_community_model()
        if not Community.is_user_with_username_banned_from_community_with_name(username=username,
                                                                               community_name=community_name):
            raise ValidationError(
                _('Can\'t unban a not-banned user.'),
            )

    def _check_can_add_administrator_with_username_to_community_with_name(self, username, community_name):
        if not self.is_creator_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('Only the creator of the community can add other administrators.'),
            )

        Community = get_community_model()

        if Community.is_user_with_username_administrator_of_community_with_name(username=username,
                                                                                community_name=community_name):
            raise ValidationError(
                _('User is already an administrator.'),
            )

        if not Community.is_user_with_username_member_of_community_with_name(username=username,
                                                                             community_name=community_name):
            raise ValidationError(
                _('Can\'t make administrator a user that is not part of the community.'),
            )

    def _check_can_remove_administrator_with_username_to_community_with_name(self, username, community_name):
        if not self.is_creator_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('Only the creator of the community can remove other administrators.'),
            )

        Community = get_community_model()

        if not Community.is_user_with_username_administrator_of_community_with_name(username=username,
                                                                                    community_name=community_name):
            raise ValidationError(
                _('User to remove is not an administrator.'),
            )

    def _check_can_get_community_with_name_administrators(self, community_name):
        # Anyone can get the administrators of the community
        return True

    def _check_can_add_moderator_with_username_to_community_with_name(self, username, community_name):
        if not self.is_administrator_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('Only administrators of the community can add other moderators.'),
            )

        Community = get_community_model()

        if Community.is_user_with_username_administrator_of_community_with_name(username=username,
                                                                                community_name=community_name):
            raise ValidationError(
                _('User is an administrator.'),
            )

        if Community.is_user_with_username_moderator_of_community_with_name(username=username,
                                                                            community_name=community_name):
            raise ValidationError(
                _('User is already a moderator.'),
            )

        if not Community.is_user_with_username_member_of_community_with_name(username=username,
                                                                             community_name=community_name):
            raise ValidationError(
                _('Can\'t make moderator a user that is not part of the community.'),
            )

    def _check_can_remove_moderator_with_username_to_community_with_name(self, username, community_name):
        if not self.is_administrator_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('Only administrators of the community can remove other moderators.'),
            )

        Community = get_community_model()

        if not Community.is_user_with_username_moderator_of_community_with_name(username=username,
                                                                                community_name=community_name):
            raise ValidationError(
                _('User to remove is not an moderator.'),
            )

    def _check_can_get_community_with_name_moderators(self, community_name):
        # Anyone can see community moderators
        return True

    def _check_can_update_circle_with_id(self, circle_id):
        if not self.has_circle_with_id(circle_id):
            raise ValidationError(
                _('Can\'t update a circle that does not belong to you.'),
            )

        if self.is_world_circle_id(circle_id):
            raise ValidationError(
                _('Can\'t update the world circle.'),
            )

        if self.is_connections_circle_id(circle_id):
            raise ValidationError(
                _('Can\'t update the connections circle.'),
            )

    def _check_can_delete_circle_with_id(self, circle_id):
        if not self.has_circle_with_id(circle_id):
            raise ValidationError(
                _('Can\'t delete a circle that does not belong to you.'),
            )

        if self.is_world_circle_id(circle_id):
            raise ValidationError(
                _('Can\'t delete the world circle.'),
            )

        if self.is_connections_circle_id(circle_id):
            raise ValidationError(
                _('Can\'t delete the connections circle.'),
            )

    def _check_can_get_circle_with_id(self, circle_id):
        if not self.has_circle_with_id(circle_id):
            raise ValidationError(
                _('Can\'t view a circle that does not belong to you.'),
            )

    def _check_can_get_list_with_id(self, list_id):
        if not self.has_list_with_id(list_id):
            raise ValidationError(
                _('Can\'t view a list that does not belong to you.'),
            )

    def _check_circle_name_not_taken(self, circle_name):
        if self.has_circle_with_name(circle_name):
            raise ValidationError(
                _('You already have a circle with that name.'),
            )

    def _check_list_name_not_taken(self, list_name):
        if self.has_list_with_name(list_name):
            raise ValidationError(
                _('You already have a list with that name.'),
            )

    def _check_can_create_community_with_name(self, name):
        self._check_community_name_not_taken(name)

    def _check_community_name_not_taken(self, community_name):
        Community = get_community_model()
        if Community.is_name_taken(community_name):
            raise ValidationError(
                _('A community with that name already exists.'),
            )

    def _check_can_favorite_community_with_name(self, community_name):
        if not self.is_member_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You must be member of a community before making it a favorite.'),
            )

        if self.has_favorite_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You have already marked this community as favorite.'),
            )

    def _check_can_unfavorite_community_with_name(self, community_name):
        if not self.has_favorite_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You have not favorited the community.'),
            )

    def _check_can_read_notification_with_id(self, notification_id):
        if not self.has_notification_with_id(notification_id=notification_id):
            raise ValidationError(
                _('You cannot mark as read a notification that doesn\'t belong to you.'),
            )

    def _check_can_delete_notification_with_id(self, notification_id):
        self._check_has_notification_with_id(notification_id=notification_id)

    def _check_has_notification_with_id(self, notification_id):
        if not self.has_notification_with_id(notification_id=notification_id):
            raise ValidationError(
                _('This notification does not belong to you.'),
            )

    def _check_can_update_device_with_uuid(self, device_uuid):
        self._check_has_device_with_uuid(device_uuid=device_uuid)

    def _check_can_delete_device_with_uuid(self, device_uuid):
        self._check_has_device_with_uuid(device_uuid=device_uuid)

    def _check_can_get_device_with_uuid(self, device_uuid):
        self._check_has_device_with_uuid(device_uuid=device_uuid)

    def _check_has_device_with_uuid(self, device_uuid):
        if not self.has_device_with_uuid(device_uuid=device_uuid):
            raise NotFound(
                _('Device not found'),
            )

    def _check_can_mute_post_with_id(self, post_id):
        if self.has_muted_post_with_id(post_id=post_id):
            raise ValidationError(
                _('Post already muted'),
            )
        self._check_can_see_post_with_id(post_id=post_id)

    def _check_can_unmute_post_with_id(self, post_id):
        self._check_has_muted_post_with_id(post_id=post_id)

    def _check_has_muted_post_with_id(self, post_id):
        if not self.has_muted_post_with_id(post_id=post_id):
            raise ValidationError(
                _('Post is not muted'),
            )

    def _check_has_post_with_id(self, post_id):
        if not self.has_post_with_id(post_id):
            raise PermissionDenied(
                _('This post does not belong to you.'),
            )

    def _check_password_matches(self, password):
        if not self.check_password(password):
            raise AuthenticationFailed(
                _('Wrong password.'),
            )

    def _check_device_with_uuid_does_not_exist(self, device_uuid):
        if self.devices.filter(uuid=device_uuid).exists():
            raise ValidationError('Device already exists')


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='bootstrap_auth_token')
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """"
    Create a token for all users
    """
    if created:
        bootstrap_user_auth_token(instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='bootstrap_user_circles')
def bootstrap_circles(sender, instance=None, created=False, **kwargs):
    """"
    Bootstrap the user circles
    """
    if created:
        bootstrap_user_circles(instance)


class UserProfile(models.Model):
    name = models.CharField(_('name'), max_length=settings.PROFILE_NAME_MAX_LENGTH, blank=False, null=False,
                            validators=[name_characters_validator])
    location = models.CharField(_('location'), max_length=settings.PROFILE_LOCATION_MAX_LENGTH, blank=False, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    is_of_legal_age = models.BooleanField(default=False)
    avatar = ProcessedImageField(verbose_name=_('avatar'), blank=False, null=True, format='JPEG',
                                 options={'quality': 50}, processors=[ResizeToFill(500, 500)],
                                 upload_to=upload_to_user_avatar_directory)
    cover = ProcessedImageField(verbose_name=_('cover'), blank=False, null=True, format='JPEG', options={'quality': 50},
                                upload_to=upload_to_user_cover_directory,
                                processors=[ResizeToFit(width=1024, upscale=False)])
    bio = models.CharField(_('bio'), max_length=settings.PROFILE_BIO_MAX_LENGTH, blank=False, null=True)
    url = models.URLField(_('url'), blank=False, null=True)
    followers_count_visible = models.BooleanField(_('followers count visible'), blank=False, null=False, default=False)
    badges = models.ManyToManyField(Badge, related_name='users_profiles')

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('users profiles')

    def __repr__(self):
        return '<UserProfile %s>' % self.user.username

    def __str__(self):
        return self.user.username


class UserNotificationsSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='notifications_settings')
    post_comment_notifications = models.BooleanField(_('post comment notifications'), default=True)
    post_reaction_notifications = models.BooleanField(_('post reaction notifications'), default=True)
    follow_notifications = models.BooleanField(_('follow notifications'), default=True)
    connection_request_notifications = models.BooleanField(_('connection request notifications'), default=True)
    connection_confirmed_notifications = models.BooleanField(_('connection confirmed notifications'), default=True)
    community_invite_notifications = models.BooleanField(_('community invite notifications'), default=True)

    @classmethod
    def create_notifications_settings(cls, user):
        return UserNotificationsSettings.objects.create(user=user)

    def update(self, post_comment_notifications=None, post_reaction_notifications=None,
               follow_notifications=None, connection_request_notifications=None,
               connection_confirmed_notifications=None, community_invite_notifications=None):

        if post_comment_notifications is not None:
            self.post_comment_notifications = post_comment_notifications

        if post_reaction_notifications is not None:
            self.post_reaction_notifications = post_reaction_notifications

        if follow_notifications is not None:
            self.follow_notifications = follow_notifications

        if connection_request_notifications is not None:
            self.connection_request_notifications = connection_request_notifications

        if connection_confirmed_notifications is not None:
            self.connection_confirmed_notifications = connection_confirmed_notifications

        if community_invite_notifications is not None:
            self.community_invite_notifications = community_invite_notifications

        self.save()


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='bootstrap_notifications_settings')
def create_user_notifications_settings(sender, instance=None, created=False, **kwargs):
    """"
    Create a user notifications settings for users
    """
    if created:
        bootstrap_user_notifications_settings(instance)


def bootstrap_user_circles(user):
    Circle = get_circle_model()
    Circle.bootstrap_circles_for_user(user)


def bootstrap_user_notifications_settings(user):
    return UserNotificationsSettings.create_notifications_settings(user=user)


def bootstrap_user_auth_token(user):
    return Token.objects.create(user=user)


def bootstrap_user_profile(user, name, is_of_legal_age, avatar=None, ):
    return UserProfile.objects.create(name=name, user=user, avatar=avatar, is_of_legal_age=is_of_legal_age, )
