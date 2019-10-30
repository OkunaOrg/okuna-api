import secrets
from datetime import datetime, timedelta
import re
import uuid
from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import six, timezone, translation
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from imagekit.models import ProcessedImageField
from pilkit.processors import ResizeToFill, ResizeToFit
from rest_framework.authtoken.models import Token
from django.db.models import Q, F, Count
from django.core.mail import EmailMultiAlternatives

from openbook.settings import USERNAME_MAX_LENGTH
from openbook_auth.helpers import upload_to_user_cover_directory, upload_to_user_avatar_directory
from openbook_notifications.helpers import get_notification_language_code_for_target_user
from openbook_translation import translation_strategy
from openbook_common.helpers import get_supported_translation_language
from openbook_common.models import Badge, Language
from openbook_common.utils.helpers import delete_file_field
from openbook_common.utils.model_loaders import get_connection_model, get_circle_model, get_follow_model, \
    get_list_model, get_community_invite_model, \
    get_post_comment_notification_model, get_follow_notification_model, get_connection_confirmed_notification_model, \
    get_connection_request_notification_model, get_post_reaction_notification_model, get_device_model, \
    get_post_mute_model, get_community_invite_notification_model, get_user_block_model, get_emoji_model, \
    get_post_comment_reply_notification_model, get_moderated_object_model, get_moderation_report_model, \
    get_moderation_penalty_model, get_post_comment_mute_model, get_post_comment_reaction_model, \
    get_post_comment_reaction_notification_model, get_top_post_model, get_top_post_community_exclusion_model
from openbook_common.validators import name_characters_validator
from openbook_notifications import helpers
from openbook_auth.checkers import *


class User(AbstractUser):
    """"
    Custom user model to change behaviour of the default user model
    such as validation and required fields.
    """
    moderated_object = GenericRelation('openbook_moderation.ModeratedObject', related_query_name='users')
    first_name = None
    last_name = None
    language = models.ForeignKey('openbook_common.Language', null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='users')
    translation_language = models.ForeignKey('openbook_common.Language', null=True, blank=True,
                                             on_delete=models.SET_NULL, related_name='translation_users')
    email = models.EmailField(_('email address'), unique=True, null=False, blank=False)
    connections_circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.CASCADE, related_name='+',
                                           null=True, blank=True)

    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()
    is_email_verified = models.BooleanField(default=False)
    are_guidelines_accepted = models.BooleanField(default=False)
    # This only happens if the user was reported and found with critical severity content and its account deleted
    is_deleted = models.BooleanField(
        _('is deleted'),
        default=False,
    )

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
    invite_count = models.SmallIntegerField(default=0)

    JWT_TOKEN_TYPE_CHANGE_EMAIL = 'CE'
    JWT_TOKEN_TYPE_PASSWORD_RESET = 'PR'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @classmethod
    def create_user(cls, username, email=None, password=None, name=None, avatar=None, is_of_legal_age=None,
                    are_guidelines_accepted=None,
                    badge=None):

        if not is_of_legal_age:
            raise ValidationError(
                _('You must confirm you are over 16 years old to make an account'),
            )

        if not are_guidelines_accepted:
            raise ValidationError(
                _('You must accept the guidelines to make an account'),
            )

        new_user = cls.objects.create_user(username, email=email, password=password,
                                           are_guidelines_accepted=are_guidelines_accepted)
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
    def get_user_with_email(cls, user_email):
        return cls.objects.get(email=user_email)

    @classmethod
    def user_with_username_exists(cls, username):
        return User.objects.filter(username=username, is_deleted=False).exists()

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

    @classmethod
    def get_unauthenticated_public_posts_for_user_with_username(cls, username, max_id=None, min_id=None):
        Circle = get_circle_model()
        world_circle_id = Circle.get_world_circle_id()

        final_query = Q(creator__username=username, circles__id=world_circle_id)

        if max_id:
            final_query.add(Q(id__lt=max_id), Q.AND)
        elif min_id:
            final_query.add(Q(id__gt=min_id), Q.AND)

        Post = get_post_model()
        result = Post.objects.filter(final_query)

        return result

    def count_posts(self):
        return self.posts.count()

    def count_moderation_penalties_for_moderation_severity(self, moderation_severity):
        return self.moderation_penalties.filter(
            moderated_object__category__severity=moderation_severity).count()

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
        check_password_matches(user=self, password=password)
        self.delete()

    def save(self, *args, **kwargs):
        self.full_clean(exclude=['invite_count'])
        return super(User, self).save(*args, **kwargs)

    def soft_delete(self):
        for post in self.posts.all().iterator():
            post.soft_delete()

        for community in self.created_communities.all().iterator():
            community.soft_delete()

        self.is_deleted = True
        self.save()

    def unsoft_delete(self):
        for post in self.posts.all.iterator():
            post.unsoft_delete()

        for community in self.created_communities.all().iterator():
            community.unsoft_delete()

        self.is_deleted = False
        self.save()

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
        check_username_not_taken(user=self, username=username)
        self.username = username
        self.save()

    def update_password(self, password):
        self.set_password(password)
        self._reset_auth_token()
        self.save()

    def request_email_update(self, email):
        check_email_not_taken(user=self, email=email)
        self.save()
        verify_token = self._make_email_verification_token_for_email(new_email=email)
        return verify_token

    def verify_email_with_token(self, token):
        new_email = check_email_verification_token_is_valid_for_email(user=self, email_verification_token=token)
        self.email = new_email
        self.save()

    def accept_guidelines(self):
        check_can_accept_guidelines(user=self)
        self.are_guidelines_accepted = True
        self.save()

    def set_language_with_id(self, language_id):
        check_can_set_language_with_id(user=self, language_id=language_id)
        Language = get_language_model()
        language = Language.objects.get(pk=language_id)
        self.language = language
        self.translation_language = get_supported_translation_language(language.code)
        self.save()

    def verify_password_reset_token(self, token, password):
        check_password_reset_verification_token_is_valid(user=self, password_verification_token=token)
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
               community_posts_visible=None,
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

        if community_posts_visible is not None:
            profile.community_posts_visible = community_posts_visible

        if save:
            profile.save()
            self.save()

    def update_notifications_settings(self, post_comment_notifications=None, post_reaction_notifications=None,
                                      follow_notifications=None, connection_request_notifications=None,
                                      connection_confirmed_notifications=None,
                                      community_invite_notifications=None,
                                      post_comment_reaction_notifications=None,
                                      post_comment_reply_notifications=None,
                                      post_comment_user_mention_notifications=None,
                                      post_user_mention_notifications=None,
                                      ):

        notifications_settings = self.notifications_settings

        notifications_settings.update(
            post_comment_notifications=post_comment_notifications,
            post_reaction_notifications=post_reaction_notifications,
            follow_notifications=follow_notifications,
            connection_request_notifications=connection_request_notifications,
            connection_confirmed_notifications=connection_confirmed_notifications,
            community_invite_notifications=community_invite_notifications,
            post_comment_reaction_notifications=post_comment_reaction_notifications,
            post_comment_reply_notifications=post_comment_reply_notifications,
            post_comment_user_mention_notifications=post_comment_user_mention_notifications,
            post_user_mention_notifications=post_user_mention_notifications,
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
        return self.connections.filter(
            target_connection__user_id=user_id).exists()

    def is_connected_with_user_with_username(self, username):
        return self.connections.filter(
            target_connection__user__username=username).exists()

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
            lists__id=list_id).exists()

    def is_world_circle_id(self, id):
        world_circle_id = self._get_world_circle_id()
        return world_circle_id == id

    def is_connections_circle_id(self, id):
        return self.connections_circle_id == id

    def has_circle_with_id(self, circle_id):
        return self.circles.filter(id=circle_id).exists()

    def has_circle_with_name(self, circle_name):
        return self.circles.filter(name=circle_name).exists()

    def has_post(self, post):
        return post.creator_id == self.pk

    def has_muted_post_with_id(self, post_id):
        return self.post_mutes.filter(post_id=post_id).exists()

    def has_muted_post_comment_with_id(self, post_comment_id):
        return self.post_comment_mutes.filter(post_comment_id=post_comment_id).exists()

    def has_blocked_user_with_id(self, user_id):
        return self.user_blocks.filter(blocked_user_id=user_id).exists()

    def is_blocked_with_user_with_id(self, user_id):
        UserBlock = get_user_block_model()
        return UserBlock.users_are_blocked(user_a_id=self.pk, user_b_id=user_id)

    def has_circles_with_ids(self, circles_ids):
        return self.circles.filter(id__in=circles_ids).count() == len(circles_ids)

    def has_list_with_id(self, list_id):
        return self.lists.filter(id=list_id).exists()

    def has_invited_user_with_username_to_community_with_name(self, username, community_name):
        return self.created_communities_invites.filter(invited_user__username=username,
                                                       community__name=community_name).exists()

    def is_administrator_of_community_with_name(self, community_name):
        return self.communities_memberships.filter(community__name=community_name, is_administrator=True).exists()

    def is_staff_of_community_with_name(self, community_name):
        return self.is_administrator_of_community_with_name(
            community_name=community_name) or self.is_moderator_of_community_with_name(community_name=community_name)

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

    def is_suspended(self):
        ModerationPenalty = get_moderation_penalty_model()
        return self.moderation_penalties.filter(type=ModerationPenalty.TYPE_SUSPENSION,
                                                expiration__gt=timezone.now()).exists()

    def get_longest_moderation_suspension(self):
        return self.moderation_penalties.order_by('expiration')[0:1][0]

    def is_global_moderator(self):
        moderators_community_name = settings.MODERATORS_COMMUNITY_NAME
        return self.is_member_of_community_with_name(community_name=moderators_community_name)

    def is_invited_to_community_with_name(self, community_name):
        Community = get_community_model()
        return Community.is_user_with_username_invited_to_community_with_name(username=self.username,
                                                                              community_name=community_name)

    def has_reported_moderated_object_with_id(self, moderated_object_id):
        ModeratedObject = get_moderated_object_model()
        ModerationReport = get_moderation_report_model()
        return ModerationReport.objects.filter(reporter_id=self.pk,
                                               moderated_object__object_id=moderated_object_id,
                                               moderated_object__object_type=ModeratedObject.OBJECT_TYPE_MODERATED_OBJECT
                                               ).exists()

    def has_favorite_community_with_name(self, community_name):
        return self.favorite_communities.filter(name=community_name).exists()

    def has_excluded_community_with_name(self, community_name):
        return self.top_posts_community_exclusions.filter(community__name=community_name).exists()

    def has_list_with_name(self, list_name):
        return self.lists.filter(name=list_name).exists()

    def has_lists_with_ids(self, lists_ids):
        return self.lists.filter(id__in=lists_ids).count() == len(lists_ids)

    def has_reacted_to_post_with_id(self, post_id, emoji_id=None):
        has_reacted_query = Q(post_id=post_id)

        if emoji_id:
            has_reacted_query.add(Q(emoji_id=emoji_id), Q.AND)

        return self.post_reactions.filter(has_reacted_query).exists()

    def has_reacted_to_post_comment_with_id(self, post_comment_id, emoji_id=None):
        has_reacted_query = Q(post_comment_id=post_comment_id)

        if emoji_id:
            has_reacted_query.add(Q(emoji_id=emoji_id), Q.AND)

        return self.post_comment_reactions.filter(has_reacted_query).exists()

    def has_commented_post_with_id(self, post_id):
        return self.posts_comments.filter(post_id=post_id).exists()

    def has_notification_with_id(self, notification_id):
        return self.notifications.filter(pk=notification_id).exists()

    def has_device_with_uuid(self, device_uuid):
        return self.devices.filter(uuid=device_uuid).exists()

    def has_follow_notifications_enabled(self):
        return self.notifications_settings.follow_notifications

    def has_post_comment_mention_notifications_enabled(self):
        return self.notifications_settings.post_comment_user_mention_notifications

    def has_post_mention_notifications_enabled(self):
        return self.notifications_settings.post_user_mention_notifications

    def has_reaction_notifications_enabled_for_post_with_id(self, post_id):
        return self.notifications_settings.post_reaction_notifications and not self.has_muted_post_with_id(
            post_id=post_id)

    def has_reaction_notifications_enabled_for_post_comment(self, post_comment):
        return self.notifications_settings.post_comment_reaction_notifications and not self.has_muted_post_with_id(
            post_id=post_comment.post_id) and not self.has_muted_post_comment_with_id(
            post_comment_id=post_comment.id)

    def has_comment_notifications_enabled_for_post_with_id(self, post_id):
        return self.notifications_settings.post_comment_notifications and not self.has_muted_post_with_id(
            post_id=post_id)

    def has_reply_notifications_enabled_for_post_comment(self, post_comment):
        return self.notifications_settings.post_comment_reply_notifications and not self.has_muted_post_with_id(
            post_id=post_comment.post_id) and not self.has_muted_post_comment_with_id(
            post_comment_id=post_comment.id)

    def has_connection_request_notifications_enabled(self):
        return self.notifications_settings.connection_request_notifications

    def has_community_invite_notifications_enabled(self):
        return self.notifications_settings.community_invite_notifications

    def has_connection_confirmed_notifications_enabled(self):
        return self.notifications_settings.connection_confirmed_notifications

    def has_reported_post_comment_with_id(self, post_comment_id):
        ModeratedObject = get_moderated_object_model()
        ModerationReport = get_moderation_report_model()
        return ModerationReport.objects.filter(reporter_id=self.pk,
                                               moderated_object__object_id=post_comment_id,
                                               moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT
                                               ).exists()

    def has_reported_post_with_id(self, post_id):
        ModeratedObject = get_moderated_object_model()
        ModerationReport = get_moderation_report_model()
        return ModerationReport.objects.filter(reporter_id=self.pk,
                                               moderated_object__object_id=post_id,
                                               moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST
                                               ).exists()

    def has_reported_user_with_id(self, user_id):
        ModeratedObject = get_moderated_object_model()
        ModerationReport = get_moderation_report_model()
        return ModerationReport.objects.filter(reporter_id=self.pk,
                                               moderated_object__object_id=user_id,
                                               moderated_object__object_type=ModeratedObject.OBJECT_TYPE_USER
                                               ).exists()

    def has_reported_community_with_id(self, community_id):
        ModeratedObject = get_moderated_object_model()
        ModerationReport = get_moderation_report_model()
        return ModerationReport.objects.filter(reporter_id=self.pk,
                                               moderated_object__object_id=community_id,
                                               moderated_object__object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY
                                               ).exists()

    def has_profile_community_posts_visible(self):
        return self.profile.community_posts_visible

    def can_see_post(self, post):
        # Check if post is public
        if post.community:
            if self._can_see_community_post(community=post.community, post=post):
                return True
        elif post.creator_id == self.pk and not post.is_deleted:
            return True
        else:
            # Check if we can retrieve the post
            if self._can_see_post(post=post):
                return True

        return False

    def can_see_post_comment(self, post_comment):
        post = post_comment.post
        if not self.can_see_post(post=post):
            return False
        post_comment_query = self._make_get_post_comment_with_id_query(post_comment_id=post_comment.pk,
                                                                       post_comment_parent_id=post_comment.parent_comment_id,
                                                                       post=post)
        PostComment = get_post_comment_model()
        return PostComment.objects.filter(post_comment_query).exists()

    def get_lists_for_follow_for_user_with_id(self, user_id):
        check_is_following_user_with_id(user=self, user_id=user_id)
        follow = self.get_follow_for_user_with_id(user_id)
        return follow.lists

    def get_circles_for_connection_with_user_with_id(self, user_id):
        check_is_connected_with_user_with_id(user=self, user_id=user_id)
        connection = self.get_connection_for_user_with_id(user_id)
        return connection.circles

    def get_reaction_for_post_with_id(self, post_id):
        return self.post_reactions.filter(post_id=post_id).get()

    def get_reactions_for_post_with_id(self, post_id, max_id=None, emoji_id=None):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)

        return self.get_reactions_for_post(post=post, max_id=max_id, emoji_id=emoji_id)

    def get_reactions_for_post(self, post, max_id=None, emoji_id=None):
        check_can_get_reactions_for_post(user=self, post=post)

        reactions_query = self._make_get_reactions_for_post_query(post=post, emoji_id=emoji_id, max_id=max_id)

        PostReaction = get_post_reaction_model()
        return PostReaction.objects.filter(reactions_query)

    def get_emoji_counts_for_post_with_id(self, post_id, emoji_id=None):
        Post = get_post_model()
        post = Post.objects.select_related('community').get(pk=post_id)
        return self.get_emoji_counts_for_post(post=post, emoji_id=emoji_id)

    def get_emoji_counts_for_post(self, post, emoji_id=None):
        check_can_get_reactions_for_post(user=self, post=post)

        Emoji = get_emoji_model()

        emoji_query = Q(post_reactions__post_id=post.pk, )

        if emoji_id:
            emoji_query.add(Q(post_reactions__emoji_id=emoji_id), Q.AND)

        post_community = post.community

        if post_community:
            if not self.is_staff_of_community_with_name(community_name=post_community.name):
                # Exclude blocked users reactions
                blocked_users_query = ~Q(Q(post_reactions__reactor__blocked_by_users__blocker_id=self.pk) | Q(
                    post_reactions__reactor__user_blocks__blocked_user_id=self.pk))
                blocked_users_query_staff_members = Q(
                    post_reactions__reactor__communities_memberships__community_id=post_community.pk)
                blocked_users_query_staff_members.add(
                    Q(post_reactions__reactor__communities_memberships__is_administrator=True) | Q(
                        post_reactions__reactor__communities_memberships__is_moderator=True), Q.AND)

                blocked_users_query.add(~blocked_users_query_staff_members, Q.AND)
                emoji_query.add(blocked_users_query, Q.AND)
        else:
            # Show all, even blocked users reactions
            blocked_users_query = ~Q(Q(post_reactions__reactor__blocked_by_users__blocker_id=self.pk) | Q(
                post_reactions__reactor__user_blocks__blocked_user_id=self.pk))
            emoji_query.add(blocked_users_query, Q.AND)

        emojis = Emoji.objects.filter(emoji_query).annotate(Count('post_reactions')).distinct().order_by(
            '-post_reactions__count').cache().all()

        return [{'emoji': emoji, 'count': emoji.post_reactions__count} for emoji in emojis]

    def get_emoji_counts_for_post_comment_with_id(self, post_comment_id, emoji_id=None):
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        return self.get_emoji_counts_for_post_comment(post_comment=post_comment, emoji_id=emoji_id)

    def get_emoji_counts_for_post_comment(self, post_comment, emoji_id=None):
        check_can_get_reactions_for_post_comment(user=self, post_comment=post_comment)

        Emoji = get_emoji_model()

        emoji_query = Q(post_comment_reactions__post_comment_id=post_comment.pk, )

        if emoji_id:
            emoji_query.add(Q(post_comment_reactions__emoji_id=emoji_id), Q.AND)

        post_comment_community = post_comment.post.community

        if post_comment_community:
            if not self.is_staff_of_community_with_name(community_name=post_comment_community.name):
                # Exclude blocked users reactions
                blocked_users_query = ~Q(Q(post_comment_reactions__reactor__blocked_by_users__blocker_id=self.pk) | Q(
                    post_comment_reactions__reactor__user_blocks__blocked_user_id=self.pk))
                blocked_users_query_staff_members = Q(
                    post_comment_reactions__reactor__communities_memberships__community_id=post_comment_community.pk)
                blocked_users_query_staff_members.add(
                    Q(post_comment_reactions__reactor__communities_memberships__is_administrator=True) | Q(
                        post_comment_reactions__reactor__communities_memberships__is_moderator=True), Q.AND)

                blocked_users_query.add(~blocked_users_query_staff_members, Q.AND)
                emoji_query.add(blocked_users_query, Q.AND)
        else:
            # Show all, even blocked users reactions
            blocked_users_query = ~Q(Q(post_comment_reactions__reactor__blocked_by_users__blocker_id=self.pk) | Q(
                post_comment_reactions__reactor__user_blocks__blocked_user_id=self.pk))
            emoji_query.add(blocked_users_query, Q.AND)

        emojis = Emoji.objects.filter(emoji_query).annotate(Count('post_comment_reactions')).distinct().order_by(
            '-post_comment_reactions__count').cache().all()

        return [{'emoji': emoji, 'count': emoji.post_comment_reactions__count} for emoji in emojis]

    def get_reaction_for_post_comment_with_id(self, post_comment_id):
        return self.post_comment_reactions.filter(post_comment_id=post_comment_id).get()

    def get_reactions_for_post_comment_with_id(self, post_comment_id, max_id=None, emoji_id=None):
        Post_comment = get_post_comment_model()
        post_comment = Post_comment.objects.get(pk=post_comment_id)

        return self.get_reactions_for_post_comment(post_comment=post_comment, max_id=max_id, emoji_id=emoji_id)

    def get_reactions_for_post_comment(self, post_comment, max_id=None, emoji_id=None):
        check_can_get_reactions_for_post_comment(user=self, post_comment=post_comment)

        reactions_query = self._make_get_reactions_for_post_comment_query(post_comment=post_comment,
                                                                          emoji_id=emoji_id, max_id=max_id)

        PostCommentReaction = get_post_comment_reaction_model()
        return PostCommentReaction.objects.filter(reactions_query)

    def react_to_post_with_id(self, post_id, emoji_id):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        return self.react_to_post(post=post, emoji_id=emoji_id)

    def react_to_post(self, post, emoji_id):
        check_can_react_to_post(user=self, post=post)
        check_can_react_with_emoji_id(user=self, emoji_id=emoji_id)

        post_id = post.pk

        if self.has_reacted_to_post_with_id(post_id):
            post_reaction = self.post_reactions.get(post_id=post_id)
            post_reaction.emoji_id = emoji_id
            post_reaction.save()
        else:
            post_reaction = post.react(reactor=self, emoji_id=emoji_id)
            if post_reaction.post.creator_id != self.pk:
                if post.creator.has_reaction_notifications_enabled_for_post_with_id(post_id=post.pk) and \
                        not post.creator.has_blocked_user_with_id(self.pk):
                    self._create_post_reaction_notification(post_reaction=post_reaction)
                self._send_post_reaction_push_notification(post_reaction=post_reaction)

        return post_reaction

    def delete_reaction_with_id_for_post_with_id(self, post_reaction_id, post_id):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        check_can_delete_reaction_with_id_for_post(user=self, post_reaction_id=post_reaction_id, post=post)
        PostReaction = get_post_reaction_model()
        post_reaction = PostReaction.objects.filter(pk=post_reaction_id).get()
        self._delete_post_reaction_notification(post_reaction=post_reaction)
        post_reaction.delete()

    def react_to_post_comment_with_id(self, post_comment_id, emoji_id):
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        return self.react_to_post_comment(post_comment=post_comment, emoji_id=emoji_id)

    def react_to_post_comment(self, post_comment, emoji_id):
        check_can_react_to_post_comment(user=self, post_comment=post_comment, emoji_id=emoji_id)

        post_comment_id = post_comment.pk

        if self.has_reacted_to_post_comment_with_id(post_comment_id):
            post_comment_reaction = self.post_comment_reactions.get(post_comment_id=post_comment_id)
            post_comment_reaction.emoji_id = emoji_id
            post_comment_reaction.save()
        else:
            post_comment_reaction = post_comment.react(reactor=self, emoji_id=emoji_id)
            if post_comment_reaction.post_comment.commenter_id != self.pk:
                commenter_has_reaction_notifications_enabled = post_comment.commenter.has_reaction_notifications_enabled_for_post_comment(
                    post_comment=post_comment)

                if commenter_has_reaction_notifications_enabled:
                    self._send_post_comment_reaction_push_notification(post_comment_reaction=post_comment_reaction)
                self._create_post_comment_reaction_notification(post_comment_reaction=post_comment_reaction)

        return post_comment_reaction

    def delete_post_comment_reaction_with_id(self, post_comment_reaction_id):
        PostCommentReaction = get_post_comment_reaction_model()
        post_comment_reaction = PostCommentReaction.objects.filter(pk=post_comment_reaction_id).get()
        return self.delete_post_comment_reaction(post_comment_reaction=post_comment_reaction)

    def delete_post_comment_reaction(self, post_comment_reaction):
        check_can_delete_post_comment_reaction(user=self, post_comment_reaction=post_comment_reaction)
        self._delete_post_comment_reaction_notification(post_comment_reaction=post_comment_reaction)
        post_comment_reaction.delete()

    def get_comments_for_post_with_id(self, post_id, min_id=None, max_id=None):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)

        check_can_get_comments_for_post(user=self, post=post)

        comments_query = self._make_get_comments_for_post_query(post=post, max_id=max_id, min_id=min_id)

        PostComment = get_post_comment_model()
        return PostComment.objects.filter(comments_query)

    def get_comment_replies_for_comment_with_id_with_post_with_uuid(self, post_comment_id, post_uuid, min_id=None,
                                                                    max_id=None):
        PostComment = get_post_comment_model()
        Post = get_post_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        post = Post.objects.get(uuid=post_uuid)
        return self.get_comment_replies_for_comment_with_post(post=post, post_comment=post_comment, min_id=min_id,
                                                              max_id=max_id)

    def get_comment_replies_for_comment_with_post(self, post, post_comment, min_id=None, max_id=None):
        check_can_get_comment_replies_for_post_and_comment(user=self, post=post, post_comment=post_comment)

        comment_replies_query = self._make_get_comments_for_post_query(post=post,
                                                                       post_comment_parent_id=post_comment.pk,
                                                                       max_id=max_id,
                                                                       min_id=min_id)
        PostComment = get_post_comment_model()
        return PostComment.objects.filter(comment_replies_query)

    def get_comments_count_for_post(self, post):
        return post.count_comments_with_user(user=self)

    def get_replies_count_for_post_comment(self, post_comment):
        return post_comment.count_replies_with_user(user=self)

    def get_status_for_post_with_uuid(self, post_uuid):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.get_status_for_post(post=post)

    def get_status_for_post(self, post):
        check_can_get_status_for_post(user=self, post=post)
        return post.status

    def enable_comments_for_post_with_id(self, post_id):
        Post = get_post_model()
        if not Post.is_post_with_id_a_community_post(post_id):
            raise ValidationError('Post is not a community post')

        post = Post.objects.select_related('community').get(pk=post_id)
        check_can_enable_disable_comments_for_post_in_community_with_name(user=self, community_name=post.community.name)
        post.community.create_enable_post_comments_log(source_user=self, target_user=post.creator, post=post)
        post.comments_enabled = True
        post.save()

        return post

    def disable_comments_for_post_with_id(self, post_id):
        Post = get_post_model()
        if not Post.is_post_with_id_a_community_post(post_id):
            raise ValidationError('Post is not a community post')

        post = Post.objects.select_related('community').get(pk=post_id)
        check_can_enable_disable_comments_for_post_in_community_with_name(user=self, community_name=post.community.name)
        post.community.create_disable_post_comments_log(source_user=self, target_user=post.creator, post=post)
        post.comments_enabled = False
        post.save()

        return post

    def comment_post_with_id(self, post_id, text):
        Post = get_post_model()
        post = Post.objects.filter(pk=post_id).get()
        return self.comment_post(post=post, text=text)

    def comment_post(self, post, text):
        check_can_comment_in_post(user=self, post=post)
        post_comment = post.comment(text=text, commenter=self)
        post_creator = post.creator
        post_commenter = self

        Post = get_post_model()

        # Language should also be prefetched here, for some reason it doesnt work....
        post_notification_target_users = Post.get_post_comment_notification_target_users(post=post,
                                                                                         post_commenter=post_commenter).only(
            'id', 'username', 'notifications_settings__post_comment_notifications')
        PostCommentNotification = get_post_comment_notification_model()

        for post_notification_target_user in post_notification_target_users:
            if post_notification_target_user.pk == post_commenter.pk or \
                    not post_notification_target_user.can_see_post_comment(post_comment=post_comment):
                continue
            post_notification_target_user_is_post_creator = post_notification_target_user.id == post_creator.id
            post_notification_target_has_comment_notifications_enabled = post_notification_target_user.has_comment_notifications_enabled_for_post_with_id(
                post_id=post_comment.post_id)

            if post_notification_target_has_comment_notifications_enabled:
                target_user_language_code = get_notification_language_code_for_target_user(
                    post_notification_target_user)
                with translation.override(target_user_language_code):
                    if post_notification_target_user_is_post_creator:
                        notification_message = {
                            "en": _('%(post_commenter_name)s · %(post_commenter_username)s commented on your post.') % {
                                'post_commenter_username': post_commenter.username,
                                'post_commenter_name': post_commenter.profile.name,
                            }}
                    else:
                        notification_message = {
                            "en": _(
                                '%(post_commenter_name)s · @%(post_commenter_username)s commented on a post you also commented on.') % {
                                      'post_commenter_username': post_commenter.username,
                                      'post_commenter_name': post_commenter.profile.name,
                                  }}

                    self._send_post_comment_push_notification(post_comment=post_comment,
                                                              notification_message=notification_message,
                                                              notification_target_user=post_notification_target_user)

            PostCommentNotification.create_post_comment_notification(post_comment_id=post_comment.pk,
                                                                     owner_id=post_notification_target_user.id)

        return post_comment

    def reply_to_comment_with_id_for_post_with_uuid(self, post_comment_id, post_uuid, text):
        PostComment = get_post_comment_model()
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        post_comment = PostComment.objects.get(pk=post_comment_id)
        return self.reply_to_comment_for_post(post_comment=post_comment, text=text, post=post)

    def reply_to_comment_for_post(self, post_comment, post, text):
        check_can_reply_to_post_comment_for_post(user=self, post_comment=post_comment, post=post)
        post_comment_reply = post_comment.reply_to_comment(text=text, commenter=self)
        comment_creator = post_comment.commenter.id
        post_creator = post.creator
        replier = self
        post = post_comment.post

        Post = get_post_model()

        # Language should also be prefetched here, for some reason it doesnt work....
        post_notification_target_users = Post.get_post_comment_reply_notification_target_users(
            post_commenter=self,
            parent_post_comment=post_comment).only(
            'id', 'username', 'notifications_settings__post_comment_reply_notifications')

        PostCommentReplyNotification = get_post_comment_reply_notification_model()

        for post_notification_target_user in post_notification_target_users:
            if post_notification_target_user.pk == replier.pk or \
                    not post_notification_target_user.can_see_post_comment(post_comment=post_comment_reply):
                continue
            post_notification_target_user_is_post_comment_creator = post_notification_target_user.id == comment_creator
            post_notification_target_user_is_post_creator = post_notification_target_user.id == post_creator.id
            post_notification_target_has_comment_reply_notifications_enabled = \
                post_notification_target_user.has_reply_notifications_enabled_for_post_comment(
                    post_comment=post_comment)

            if post_notification_target_has_comment_reply_notifications_enabled:
                target_user_language_code = get_notification_language_code_for_target_user(
                    post_notification_target_user)

                with translation.override(target_user_language_code):
                    if post_notification_target_user_is_post_comment_creator:
                        notification_message = {
                            "en": _(
                                '%(post_commenter_name)s · @%(post_commenter_username)s replied to your comment on a post.') % {
                                      'post_commenter_username': replier.username,
                                      'post_commenter_name': replier.profile.name,
                                  }}
                    elif post_notification_target_user_is_post_creator:
                        notification_message = {
                            "en": _(
                                '%(post_commenter_name)s · %(post_commenter_username)s replied to a comment on your post.') % {
                                      'post_commenter_username': replier.username,
                                      'post_commenter_name': replier.profile.name,
                                  }}
                    else:
                        notification_message = {
                            "en": _(
                                '%(post_commenter_name)s · @%(post_commenter_username)s replied on a comment you also replied on.') % {
                                      'post_commenter_username': replier.username,
                                      'post_commenter_name': replier.profile.name,
                                  }}

                    self._send_post_comment_push_notification(post_comment=post_comment_reply,
                                                              notification_message=notification_message,
                                                              notification_target_user=post_notification_target_user)

            PostCommentReplyNotification.create_post_comment_reply_notification(
                post_comment_id=post_comment_reply.pk,
                owner_id=post_notification_target_user.id)

        return post_comment_reply

    def delete_comment_with_id_for_post_with_id(self, post_comment_id, post_id):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        check_can_delete_comment_with_id_for_post(user=self, post_comment_id=post_comment_id, post=post)
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        self._delete_post_comment_notification(post_comment=post_comment)
        post_comment.delete()

    def update_comment_with_id_for_post_with_id(self, post_comment_id, post_id, text):
        check_has_post_comment_with_id(user=self, post_comment_id=post_comment_id)
        check_comments_enabled_for_post_with_id(user=self, post_id=post_id)
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        check_can_edit_comment_with_id_for_post(user=self, post_comment_id=post_comment_id, post=post)

        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        post_comment.update_comment(text)
        return post_comment

    def get_comment_with_id_for_post_with_uuid(self, post_comment_id, post_uuid):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)

        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        return self.get_comment_for_post(post_comment=post_comment, post=post)

    def get_comment_for_post(self, post, post_comment):
        check_can_get_comment_for_post(user=self, post_comment=post_comment, post=post)
        return post_comment

    def create_circle(self, name, color):
        check_circle_name_not_taken(user=self, circle_name=name)
        Circle = get_circle_model()
        circle = Circle.objects.create(name=name, creator=self, color=color)

        return circle

    def delete_circle(self, circle):
        return self.delete_circle_with_id(circle.pk)

    def delete_circle_with_id(self, circle_id):
        check_can_delete_circle_with_id(user=self, circle_id=circle_id)
        circle = self.circles.get(id=circle_id)
        circle.delete()

    def update_circle(self, circle, **kwargs):
        return self.update_circle_with_id(circle.pk, **kwargs)

    def update_circle_with_id(self, circle_id, name=None, color=None, usernames=None):
        check_can_update_circle_with_id(user=self, circle_id=circle_id)
        check_circle_data(user=self, name=name, color=color)
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
        check_is_following_user_with_id(user=self, user_id=user_id)
        check_is_connected_with_user_with_id_in_circle_with_id(user=self, user_id=user_id, circle_id=circle_id)
        connection = self.get_connection_for_user_with_id(user_id)
        connection.circles.remove(circle_id)
        return connection

    def add_circle_with_id_to_connection_with_user_with_id(self, user_id, circle_id):
        check_is_following_user_with_id(user=self, user_id=user_id)
        check_is_not_connected_with_user_with_id_in_circle_with_id(user=self, user_id=user_id, circle_id=circle_id)
        connection = self.get_connection_for_user_with_id(user_id)
        connection.circles.add(circle_id)
        return connection

    def get_circle_with_id(self, circle_id):
        check_can_get_circle_with_id(user=self, circle_id=circle_id)
        return self.circles.get(id=circle_id)

    def favorite_community_with_name(self, community_name):
        check_can_favorite_community_with_name(user=self, community_name=community_name)

        Community = get_community_model()
        community_to_favorite = Community.objects.get(name=community_name)

        self.favorite_communities.add(community_to_favorite)

        return community_to_favorite

    def unfavorite_community_with_name(self, community_name):
        check_can_unfavorite_community_with_name(user=self, community_name=community_name)

        Community = get_community_model()
        community_to_unfavorite = Community.objects.get(name=community_name)

        self.favorite_communities.remove(community_to_unfavorite)

        return community_to_unfavorite

    def create_community(self, name, title, type, color, categories_names, description=None, rules=None,
                         avatar=None, cover=None, user_adjective=None, users_adjective=None,
                         invites_enabled=None):
        check_can_create_community_with_name(user=self, name=name)

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
        check_can_delete_community_with_name(user=self, community_name=community_name)

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
        check_can_update_community_with_name(user=self, community_name=community_name)
        check_community_data(user=self, name=name)

        Community = get_community_model()
        community_to_update = Community.objects.get(name=community_name)

        community_to_update.update(name=name, title=title, description=description,
                                   color=color, type=type, user_adjective=user_adjective,
                                   users_adjective=users_adjective, rules=rules, categories_names=categories_names,
                                   invites_enabled=invites_enabled)

        return community_to_update

    def update_community_with_name_avatar(self, community_name, avatar):
        check_can_update_community_with_name(user=self, community_name=community_name)
        check_community_data(user=self, avatar=avatar)

        Community = get_community_model()
        community_to_update_avatar_from = Community.objects.get(name=community_name)
        community_to_update_avatar_from.avatar = avatar

        community_to_update_avatar_from.save()

        return community_to_update_avatar_from

    def delete_community_with_name_avatar(self, community_name):
        check_can_update_community_with_name(user=self, community_name=community_name)
        Community = get_community_model()
        community_to_delete_avatar_from = Community.objects.get(name=community_name)
        delete_file_field(community_to_delete_avatar_from.avatar)
        community_to_delete_avatar_from.avatar = None
        community_to_delete_avatar_from.save()
        return community_to_delete_avatar_from

    def update_community_with_name_cover(self, community_name, cover):
        check_can_update_community_with_name(user=self, community_name=community_name)
        check_community_data(user=self, cover=cover)

        Community = get_community_model()
        community_to_update_cover_from = Community.objects.get(name=community_name)

        community_to_update_cover_from.cover = cover

        community_to_update_cover_from.save()

        return community_to_update_cover_from

    def delete_community_with_name_cover(self, community_name):
        check_can_update_community_with_name(user=self, community_name=community_name)

        Community = get_community_model()
        community_to_delete_cover_from = Community.objects.get(name=community_name)

        delete_file_field(community_to_delete_cover_from.cover)
        community_to_delete_cover_from.cover = None
        community_to_delete_cover_from.save()
        return community_to_delete_cover_from

    def get_community_with_name_members(self, community_name, max_id=None, exclude_keywords=None):
        check_can_get_community_with_name_members(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_members(community_name=community_name, members_max_id=max_id,
                                                         exclude_keywords=exclude_keywords)

    def search_community_with_name_members(self, community_name, query, exclude_keywords=None):
        check_can_get_community_with_name_members(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_members(community_name=community_name, query=query,
                                                            exclude_keywords=exclude_keywords)

    def join_community_with_name(self, community_name):
        check_can_join_community_with_name(
            user=self,
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
        check_can_leave_community_with_name(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        community_to_leave = Community.objects.get(name=community_name)

        if self.has_favorite_community_with_name(community_name):
            self.unfavorite_community_with_name(community_name=community_name)

        community_to_leave.remove_member(self)

        return community_to_leave

    def invite_user_with_username_to_community_with_name(self, username, community_name):
        check_can_invite_user_with_username_to_community_with_name(user=self, username=username,
                                                                   community_name=community_name)

        Community = get_community_model()

        community_to_invite_user_to = Community.objects.get(name=community_name)
        user_to_invite = User.objects.get(username=username)

        community_invite = community_to_invite_user_to.create_invite(creator=self, invited_user=user_to_invite)

        self._create_community_invite_notification(community_invite)
        self._send_community_invite_push_notification(community_invite)

        return community_invite

    def uninvite_user_with_username_to_community_with_name(self, username, community_name):
        check_can_uninvite_user_with_username_to_community_with_name(user=self, username=username,
                                                                     community_name=community_name)

        community_invite = self.created_communities_invites.get(invited_user__username=username, creator=self,
                                                                community__name=community_name)
        uninvited_user = community_invite.invited_user
        community_invite.delete()

        return uninvited_user

    def get_community_with_name_administrators(self, community_name, max_id):
        check_can_get_community_with_name_administrators(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_administrators(community_name=community_name,
                                                                administrators_max_id=max_id)

    def search_community_with_name_administrators(self, community_name, query):
        check_can_get_community_with_name_administrators(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_administrators(community_name=community_name, query=query)

    def add_administrator_with_username_to_community_with_name(self, username, community_name):
        check_can_add_administrator_with_username_to_community_with_name(
            user=self,
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
        check_can_remove_administrator_with_username_to_community_with_name(
            user=self,
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
        check_can_get_community_with_name_moderators(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_moderators(community_name=community_name,
                                                            moderators_max_id=max_id)

    def search_community_with_name_moderators(self, community_name, query):
        check_can_get_community_with_name_moderators(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_moderators(community_name=community_name, query=query)

    def add_moderator_with_username_to_community_with_name(self, username, community_name):
        check_can_add_moderator_with_username_to_community_with_name(
            user=self,
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
        check_can_remove_moderator_with_username_to_community_with_name(
            user=self,
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
        check_can_get_community_with_name_banned_users(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_banned_users(community_name=community_name, users_max_id=max_id)

    def search_community_with_name_banned_users(self, community_name, query):
        check_can_get_community_with_name_banned_users(
            user=self,
            community_name=community_name)

        Community = get_community_model()
        return Community.search_community_with_name_banned_users(community_name=community_name, query=query)

    def ban_user_with_username_from_community_with_name(self, username, community_name):
        check_can_ban_user_with_username_from_community_with_name(user=self, username=username,
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
        check_can_unban_user_with_username_from_community_with_name(user=self, username=username,
                                                                    community_name=community_name)
        Community = get_community_model()

        community_to_unban_user_from = Community.objects.get(name=community_name)
        user_to_unban = User.objects.get(username=username)

        community_to_unban_user_from.banned_users.remove(user_to_unban)
        community_to_unban_user_from.create_user_unban_log(source_user=self, target_user=user_to_unban)

        return community_to_unban_user_from

    def create_list(self, name, emoji_id):
        check_list_name_not_taken(user=self, list_name=name)
        List = get_list_model()
        list = List.objects.create(name=name, creator=self, emoji_id=emoji_id)

        return list

    def delete_list(self, list):
        return self.delete_list_with_id(list.pk)

    def delete_list_with_id(self, list_id):
        check_can_delete_list_with_id(user=self, list_id=list_id)
        list = self.lists.get(id=list_id)
        list.delete()

    def update_list(self, list, **kwargs):
        return self.update_list_with_id(list.pk, **kwargs)

    def update_list_with_id(self, list_id, name=None, emoji_id=None, usernames=None):
        check_can_update_list_with_id(user=self, list_id=list_id)
        check_list_data(user=self, name=name)
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
        check_can_get_list_with_id(user=self, list_id=list_id)
        return self.lists.get(id=list_id)

    def search_users_with_query(self, query):
        users_query = self._make_search_users_query(query=query)

        return User.objects.filter(users_query)

    def _make_search_users_query(self, query):
        users_query = self._make_users_query()

        search_users_query = Q(username__icontains=query)
        search_users_query.add(Q(profile__name__icontains=query), Q.OR)

        users_query.add(search_users_query, Q.AND)
        return users_query

    def _make_users_query(self):
        users_query = Q(is_deleted=False)
        users_query.add(~Q(blocked_by_users__blocker_id=self.pk) & ~Q(user_blocks__blocked_user_id=self.pk),
                        Q.AND)
        return users_query

    def get_linked_users(self, max_id=None):
        # All users which are connected with us and we have accepted by adding
        # them to a circle
        linked_users_query = self._make_linked_users_query()

        if max_id:
            linked_users_query.add(Q(id__lt=max_id), Q.AND)

        return User.objects.filter(linked_users_query).distinct()

    def search_linked_users_with_query(self, query):
        linked_users_query = self._make_linked_users_query()

        names_query = Q(username__icontains=query)
        names_query.add(Q(profile__name__icontains=query), Q.OR)

        linked_users_query.add(names_query, Q.AND)

        return User.objects.filter(linked_users_query).distinct()

    def get_blocked_users(self, max_id=None):
        blocked_users_query = self._make_blocked_users_query(max_id=max_id)

        return User.objects.filter(blocked_users_query).distinct()

    def search_blocked_users_with_query(self, query):
        blocked_users_query = self._make_blocked_users_query()

        names_query = Q(username__icontains=query)
        names_query.add(Q(profile__name__icontains=query), Q.OR)

        blocked_users_query.add(names_query, Q.AND)

        return User.objects.filter(blocked_users_query).distinct()

    def search_top_posts_excluded_communities_with_query(self, query):

        excluded_communities_search_query = Q(user=self)
        excluded_communities_search_query.add((Q(community__title__icontains=query) |
                                               Q(community__name__icontains=query)), Q.AND)

        TopPostCommunityExclusion = get_top_post_community_exclusion_model()

        return TopPostCommunityExclusion.objects.filter(excluded_communities_search_query)

    def get_top_posts_community_exclusions(self):
        TopPostCommunityExclusion = get_top_post_community_exclusion_model()
        top_posts_community_exclusions = TopPostCommunityExclusion.objects \
            .select_related('community') \
            .filter(user=self)

        return top_posts_community_exclusions

    def get_followers(self, max_id=None):
        followers_query = self._make_followers_query()

        if max_id:
            followers_query.add(Q(id__lt=max_id), Q.AND)

        return User.objects.filter(followers_query).distinct()

    def get_followings(self, max_id=None):
        followings_query = self._make_followings_query()

        if max_id:
            followings_query.add(Q(id__lt=max_id), Q.AND)

        return User.objects.filter(followings_query).distinct()

    def search_followers_with_query(self, query):
        followers_query = Q(follows__followed_user_id=self.pk, is_deleted=False)

        names_query = Q(username__icontains=query)
        names_query.add(Q(profile__name__icontains=query), Q.OR)

        followers_query.add(names_query, Q.AND)

        return User.objects.filter(followers_query).distinct()

    def search_followings_with_query(self, query):
        followings_query = Q(followers__user_id=self.pk, is_deleted=False)

        names_query = Q(username__icontains=query)
        names_query.add(Q(profile__name__icontains=query), Q.OR)

        followings_query.add(names_query, Q.AND)

        return User.objects.filter(followings_query).distinct()

    def get_trending_posts(self):
        Post = get_post_model()
        return Post.get_trending_posts_for_user_with_id(user_id=self.pk)

    def get_trending_communities(self, category_name=None):
        Community = get_community_model()
        return Community.get_trending_communities_for_user_with_id(user_id=self.pk, category_name=category_name)

    def search_communities_with_query(self, query):
        Community = get_community_model()
        return Community.search_communities_with_query(query)

    def get_community_with_name(self, community_name):
        check_can_get_community_with_name(user=self, community_name=community_name)
        Community = get_community_model()
        return Community.get_community_with_name_for_user_with_id(community_name=community_name, user_id=self.pk)

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

    def create_public_post(self, text=None, image=None, video=None, created=None, is_draft=False):
        world_circle_id = self._get_world_circle_id()
        return self.create_encircled_post(text=text, image=image, video=video, circles_ids=[world_circle_id],
                                          created=created, is_draft=is_draft)

    def create_encircled_post(self, circles_ids, text=None, image=None, video=None, created=None, is_draft=False):
        check_can_post_to_circles_with_ids(user=self, circles_ids=circles_ids)
        Post = get_post_model()
        post = Post.create_post(text=text, creator=self, circles_ids=circles_ids, image=image, video=video,
                                created=created, is_draft=is_draft)

        return post

    def update_post_with_uuid(self, post_uuid, text=None):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.update_post(post=post, text=text)

    def update_post(self, post, text=None):
        check_can_update_post(user=self, post=post)
        post.update(text=text)
        return post

    def create_community_post(self, community_name, text=None, image=None, video=None, created=None, is_draft=False):
        check_can_post_to_community_with_name(user=self, community_name=community_name)
        Post = get_post_model()
        post = Post.create_post(text=text, creator=self, community_name=community_name, image=image, video=video,
                                created=created, is_draft=is_draft)

        return post

    def get_media_for_post_with_uuid(self, post_uuid):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.get_media_for_post(post=post)

    def get_media_for_post(self, post):
        check_can_get_media_for_post(user=self, post=post)
        return post.get_media()

    def add_media_to_post_with_uuid(self, file, post_uuid, order):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.add_media_to_post(post=post, file=file, order=order)

    def add_media_to_post(self, file, post, order=None):
        check_can_add_media_to_post(user=self, post=post)
        post.add_media(file=file, order=order)
        return post

    def publish_post_with_uuid(self, post_uuid):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.publish_post(post=post)

    def publish_post(self, post):
        check_can_publish_post(user=self, post=post)
        post.publish()
        return post

    def delete_post_with_uuid(self, post_uuid):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.delete_post(post=post)

    def delete_post(self, post):
        check_can_delete_post(user=self, post=post)
        # This method is overriden
        post.delete()

    def get_user_with_username(self, username):
        user_query = Q(username=username, is_deleted=False)
        user = User.objects.get(user_query)
        check_can_get_user_with_id(user=self, user_id=user.pk)
        return user

    def translate_post_with_id(self, post_id):
        check_can_translate_post_with_id(user=self, post_id=post_id)
        Post = get_post_model()
        post = Post.objects.get(id=post_id)
        result = translation_strategy.translate_text(
            source_language_code=post.language.code,
            target_language_code=self.translation_language.code,
            text=post.text
        )
        return post, result.get('translated_text')

    def open_post_with_id(self, post_id):
        check_can_open_post_with_id(user=self, post_id=post_id)
        Post = get_post_model()
        post = Post.objects.select_related('community').get(id=post_id)
        post.community.create_open_post_log(source_user=self, target_user=post.creator, post=post)
        post.is_closed = False
        post.save()

        return post

    def close_post_with_id(self, post_id):
        Post = get_post_model()
        post = Post.objects.select_related('community').get(id=post_id)
        return self.close_post(post=post)

    def close_post(self, post):
        check_can_close_post(user=self, post=post)
        post.community.create_close_post_log(source_user=self, target_user=post.creator, post=post)
        post.is_closed = True
        post.save()

        return post

    def get_posts_for_community_with_name(self, community_name, max_id=None):
        """
        :param community_name:
        :param max_id:
        :return:
        """
        check_can_get_posts_for_community_with_name(user=self, community_name=community_name)

        Community = get_community_model()
        community = Community.objects.get(name=community_name)

        # We don't want to see closed posts in the community timeline if we're staff members
        community_posts_query = self._make_get_community_with_id_posts_query(community=community,
                                                                             include_closed_posts_for_staff=False)

        if max_id:
            community_posts_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()
        profile_posts = Post.objects.filter(community_posts_query).distinct()

        return profile_posts

    def get_closed_posts_for_community_with_name(self, community_name, max_id=None):
        check_can_get_closed_posts_for_community_with_name(user=self, community_name=community_name)
        Community = get_community_model()
        community = Community.objects.get(name=community_name)

        posts_query = Q(community__id=community.pk, is_closed=True)

        if max_id:
            posts_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()
        profile_posts = Post.objects.filter(posts_query).distinct()

        return profile_posts

    def get_post_with_id(self, post_id):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        check_can_see_post(user=self, post=post)
        return post

    def get_posts(self, max_id=None):
        """
        Get all the posts for ourselves
        :param max_id:
        :return:
        """
        Post = get_post_model()
        ModeratedObject = get_moderated_object_model()

        posts_query = Q(creator_id=self.id, is_deleted=False, status=Post.STATUS_PUBLISHED)

        exclude_reported_and_approved_posts_query = ~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED)

        posts_query.add(exclude_reported_and_approved_posts_query, Q.AND)

        if not self.has_profile_community_posts_visible():
            posts_query.add(Q(community__isnull=True), Q.AND)

        if max_id:
            posts_query.add(Q(id__lt=max_id), Q.AND)

        posts = Post.objects.filter(posts_query)

        return posts

    def get_posts_for_user_with_username(self, username, max_id=None, min_id=None):
        user = User.objects.get(username=username)
        return self.get_posts_for_user(user=user, max_id=max_id, min_id=min_id)

    def get_posts_for_user(self, user, max_id=None, min_id=None):
        Post = get_post_model()
        Circle = get_circle_model()
        ModeratedObject = get_moderated_object_model()
        world_circle_id = Circle.get_world_circle_id()

        user_query = Q(creator_id=user.pk)

        exclude_reported_and_approved_posts_query = ~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED)

        exclude_reported_posts_query = ~Q(moderated_object__reports__reporter_id=self.pk)

        cursor_scrolling_query = Q()

        if max_id:
            cursor_scrolling_query = Q(id__lt=max_id)
        elif min_id:
            cursor_scrolling_query = Q(id__gt=min_id)

        exclude_blocked_posts_query = ~Q(Q(creator__blocked_by_users__blocker_id=self.pk) | Q(
            creator__user_blocks__blocked_user_id=self.pk))

        exclude_deleted_posts_query = Q(is_deleted=False, status=Post.STATUS_PUBLISHED)

        # Get user world circle posts

        world_circle_posts_query = Q(creator__id=user.pk, circles__id=world_circle_id)

        world_circle_posts = Post.objects.filter(
            user_query &
            world_circle_posts_query &
            exclude_deleted_posts_query &
            exclude_blocked_posts_query &
            exclude_reported_posts_query &
            exclude_reported_and_approved_posts_query &
            cursor_scrolling_query
        )

        # Get user community posts
        Community = get_community_model()
        community_posts_query = Q(creator__pk=user.pk, community__isnull=False, is_closed=False)
        exclude_private_community_posts_query = Q(community__type=Community.COMMUNITY_TYPE_PUBLIC) | Q(
            community__memberships__user__id=self.pk)

        community_posts = Post.objects.filter(
            user_query &
            community_posts_query &
            exclude_private_community_posts_query &
            exclude_deleted_posts_query &
            exclude_blocked_posts_query &
            exclude_reported_posts_query &
            exclude_reported_and_approved_posts_query &
            cursor_scrolling_query
        )

        # Get user connection circles posts
        connection_circles_query = Q(circles__connections__target_user_id=self.pk,
                                     circles__connections__target_connection__circles__isnull=False)

        connection_circles_posts = Post.objects.filter(
            user_query &
            connection_circles_query &
            exclude_deleted_posts_query &
            exclude_blocked_posts_query &
            exclude_reported_posts_query &
            exclude_reported_and_approved_posts_query &
            cursor_scrolling_query
        )

        if user.has_profile_community_posts_visible():
            results = world_circle_posts.union(community_posts, connection_circles_posts)
        else:
            results = world_circle_posts.union(connection_circles_posts)

        return results

    def exclude_community_from_top_posts(self, community):
        check_can_exclude_community(user=self, community=community)

        TopPostCommunityExclusion = get_top_post_community_exclusion_model()
        top_post_community_exclusion = TopPostCommunityExclusion(
            user=self,
            community=community
        )
        self.top_posts_community_exclusions.add(top_post_community_exclusion, bulk=False)

    def exclude_community_with_name_from_top_posts(self, community_name):
        Community = get_community_model()
        community_to_exclude = Community.objects.get(name=community_name)
        self.exclude_community_from_top_posts(community_to_exclude)

    def remove_exclusion_for_community_from_top_posts(self, community):
        check_can_remove_exclusion_for_community(user=self, community=community)

        TopPostCommunityExclusion = get_top_post_community_exclusion_model()
        TopPostCommunityExclusion.objects.get(user=self, community=community).delete()

    def remove_exclusion_for_community_with_name_from_top_posts(self, community_name):
        Community = get_community_model()
        community = Community.objects.get(name=community_name)
        self.remove_exclusion_for_community_from_top_posts(community)

    def get_top_posts(self, max_id=None, min_id=None, exclude_joined_communities=False):
        """
        Gets top posts (communities only) for authenticated user excluding reported, closed, blocked users posts
        """
        Post = get_post_model()
        TopPost = get_top_post_model()
        Community = get_community_model()

        posts_select_related = ('post__creator', 'post__creator__profile', 'post__community', 'post__image')
        posts_prefetch_related = ('post__circles', 'post__creator__profile__badges')

        posts_only = ('id',
                      'post__text', 'post__id', 'post__uuid', 'post__created', 'post__image__width',
                      'post__image__height', 'post__image__image',
                      'post__creator__username', 'post__creator__id', 'post__creator__profile__name',
                      'post__creator__profile__avatar',
                      'post__creator__profile__badges__id', 'post__creator__profile__badges__keyword',
                      'post__creator__profile__id', 'post__community__id', 'post__community__name',
                      'post__community__avatar',
                      'post__community__color', 'post__community__title')

        reported_posts_exclusion_query = ~Q(post__moderated_object__reports__reporter_id=self.pk)
        excluded_communities_query = ~Q(post__community__top_posts_community_exclusions__user=self.pk)

        top_community_posts_query = Q(post__is_closed=False,
                                      post__is_deleted=False,
                                      post__status=Post.STATUS_PUBLISHED)

        top_community_posts_query.add(~Q(Q(post__creator__blocked_by_users__blocker_id=self.pk) | Q(
            post__creator__user_blocks__blocked_user_id=self.pk)), Q.AND)
        top_community_posts_query.add(Q(post__community__type=Community.COMMUNITY_TYPE_PUBLIC), Q.AND)
        top_community_posts_query.add(~Q(post__community__banned_users__id=self.pk), Q.AND)

        if max_id:
            top_community_posts_query.add(Q(id__lt=max_id), Q.AND)
        elif min_id:
            top_community_posts_query.add(Q(id__gt=min_id), Q.AND)

        ModeratedObject = get_moderated_object_model()
        top_community_posts_query.add(~Q(post__moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

        if exclude_joined_communities:
            # exclude communities the user is a member of
            exclude_joined_communities_query = ~Q(post__community__memberships__user__id=self.pk)
            top_community_posts_query.add(exclude_joined_communities_query, Q.AND)

        top_community_posts_query.add(reported_posts_exclusion_query, Q.AND)
        top_community_posts_query.add(excluded_communities_query, Q.AND)

        top_community_posts_queryset = TopPost.objects.select_related(*posts_select_related).prefetch_related(
            *posts_prefetch_related).only(*posts_only).filter(top_community_posts_query)

        return top_community_posts_queryset

    def get_timeline_posts(self, lists_ids=None, circles_ids=None, max_id=None, min_id=None, count=None):
        """
        Get the timeline posts for self. The results will be dynamic based on follows and connections.
        """

        if not circles_ids and not lists_ids:
            return self._get_timeline_posts_with_no_filters(max_id=max_id, min_id=min_id, count=count)

        return self._get_timeline_posts_with_filters(max_id=max_id, circles_ids=circles_ids, lists_ids=lists_ids)

    def _get_timeline_posts_with_filters(self, max_id=None, min_id=None, circles_ids=None, lists_ids=None):
        Post = get_post_model()

        world_circle_id = self._get_world_circle_id()

        if circles_ids:
            timeline_posts_query = Q(creator=self.pk, circles__id__in=circles_ids)
        else:
            timeline_posts_query = Q()

        if lists_ids:
            followed_users_query = self.follows.filter(lists__id__in=lists_ids)
        else:
            followed_users_query = self.follows.all()

        followed_users = followed_users_query.values('followed_user__id').cache()

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
        elif min_id:
            timeline_posts_query.add(Q(id__gt=min_id), Q.AND)

        timeline_posts_query.add(Q(is_deleted=False, status=Post.STATUS_PUBLISHED), Q.AND)

        timeline_posts_query.add(~Q(moderated_object__reports__reporter_id=self.pk), Q.AND)

        return Post.objects.filter(timeline_posts_query).distinct()

    def _get_timeline_posts_with_no_filters(self, max_id=None, min_id=None, count=10):
        """
        Being the main action of the network, an optimised call of the get timeline posts call with no filtering.
        """
        world_circle_id = self._get_world_circle_id()

        Post = get_post_model()

        posts_select_related = ('creator', 'creator__profile', 'community', 'image')

        posts_prefetch_related = ('circles', 'creator__profile__badges')

        posts_only = ('text', 'id', 'uuid', 'created', 'image__width', 'image__height', 'image__image',
                      'creator__username', 'creator__id', 'creator__profile__name', 'creator__profile__avatar',
                      'creator__profile__badges__id', 'creator__profile__badges__keyword',
                      'creator__profile__id', 'community__id', 'community__name', 'community__avatar',
                      'community__color',
                      'community__title')

        ModeratedObject = get_moderated_object_model()
        reported_posts_exclusion_query = ~Q(moderated_object__reports__reporter_id=self.pk)

        own_posts_query = Q(creator=self.pk, community__isnull=True, is_deleted=False, status=Post.STATUS_PUBLISHED)

        own_posts_query.add(reported_posts_exclusion_query, Q.AND)

        if max_id:
            own_posts_query.add(Q(id__lt=max_id), Q.AND)

        own_posts_queryset = self.posts.select_related(*posts_select_related).prefetch_related(
            *posts_prefetch_related).only(*posts_only).filter(own_posts_query)

        community_posts_query = Q(community__memberships__user__id=self.pk, is_closed=False, is_deleted=False,
                                  status=Post.STATUS_PUBLISHED)

        community_posts_query.add(~Q(Q(creator__blocked_by_users__blocker_id=self.pk) | Q(
            creator__user_blocks__blocked_user_id=self.pk)), Q.AND)

        if max_id:
            community_posts_query.add(Q(id__lt=max_id), Q.AND)

        community_posts_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

        community_posts_query.add(reported_posts_exclusion_query, Q.AND)

        community_posts_queryset = Post.objects.select_related(*posts_select_related).prefetch_related(
            *posts_prefetch_related).only(*posts_only).filter(community_posts_query)

        followed_users = self.follows.values('followed_user_id')

        followed_users_ids = [followed_user['followed_user_id'] for followed_user in followed_users]

        followed_users_query = Q(creator__in=followed_users_ids, is_deleted=False, status=Post.STATUS_PUBLISHED)

        followed_users_query.add(reported_posts_exclusion_query, Q.AND)

        if max_id:
            followed_users_query.add(Q(id__lt=max_id), Q.AND)

        followed_users_query.add(
            Q(circles__id=world_circle_id) | Q(circles__connections__target_connection__circles__isnull=False,
                                               circles__connections__target_user=self.pk), Q.AND)

        followed_users_queryset = Post.objects.select_related(*posts_select_related).prefetch_related(
            *posts_prefetch_related).only(*posts_only).filter(followed_users_query)

        final_queryset = own_posts_queryset.union(community_posts_queryset, followed_users_queryset)

        return final_queryset

    def get_global_moderated_objects(self, types=None, max_id=None, verified=None, statuses=None):
        check_can_get_global_moderated_objects(user=self)
        ModeratedObject = get_moderated_object_model()

        moderated_objects_query = Q()

        if types:
            moderated_objects_query.add(Q(object_type__in=types), Q.AND)

        if max_id:
            moderated_objects_query.add(Q(id__lt=max_id), Q.AND)

        if verified is not None:
            moderated_objects_query.add(Q(verified=verified), Q.AND)

        if statuses is not None:
            moderated_objects_query.add(Q(status__in=statuses), Q.AND)

        return ModeratedObject.objects.filter(moderated_objects_query)

    def get_logs_for_moderated_object_with_id(self, moderated_object_id, max_id=None):
        ModeratedObject = get_moderated_object_model()
        moderated_object = ModeratedObject.objects.get(pk=moderated_object_id)
        return self.get_logs_for_moderated_object(moderated_object=moderated_object, max_id=max_id)

    def get_logs_for_moderated_object(self, moderated_object, max_id=None):
        check_can_get_moderated_object(user=self, moderated_object=moderated_object)

        query = Q()

        if max_id:
            query.add(Q(id__lt=max_id), Q.AND)

        return moderated_object.logs.filter(query)

    def get_reports_for_moderated_object_with_id(self, moderated_object_id, max_id=None):
        ModeratedObject = get_moderated_object_model()
        moderated_object = ModeratedObject.objects.get(pk=moderated_object_id)
        return self.get_reports_for_moderated_object(moderated_object=moderated_object, max_id=max_id)

    def get_reports_for_moderated_object(self, moderated_object, max_id=None):
        check_can_get_moderated_object(user=self, moderated_object=moderated_object)

        query = Q()

        if max_id:
            query.add(Q(id__lt=max_id), Q.AND)

        return moderated_object.reports.filter(query)

    def get_community_moderated_objects(self, community_name, types=None, max_id=None, verified=None, statuses=None):
        check_can_get_community_moderated_objects(user=self, community_name=community_name)
        ModeratedObject = get_moderated_object_model()

        moderated_objects_query = Q(community__name=community_name)

        if types:
            moderated_objects_query.add(Q(object_type__in=types), Q.AND)

        if verified is not None:
            moderated_objects_query.add(Q(verified=verified), Q.AND)

        if statuses is not None:
            moderated_objects_query.add(Q(status__in=statuses), Q.AND)

        if max_id:
            moderated_objects_query.add(Q(id__lt=max_id), Q.AND)

        return ModeratedObject.objects.filter(moderated_objects_query)

    def get_moderation_penalties(self, max_id=None):
        query = Q()
        if max_id:
            query.add(Q(id__lt=max_id), Q.AND)
        return self.moderation_penalties.filter(query)

    def count_active_moderation_penalties(self):
        return self.get_moderation_penalties().filter(expiration__gt=timezone.now()).count()

    def get_pending_moderated_objects_communities(self, max_id):
        """Retrieves the communities staff of that have pending moderated objects"""
        query = Q(memberships__user_id=self.pk) & (
                Q(memberships__is_moderator=True) | Q(memberships__is_administrator=True))

        ModeratedObject = get_moderated_object_model()
        query.add(Q(moderated_objects__status=ModeratedObject.STATUS_PENDING), Q.AND)

        if max_id:
            query.add(Q(id__lt=max_id), Q.AND)

        Community = get_community_model()

        return Community.objects.filter(query).distinct()

    def count_pending_communities_moderated_objects(self):
        ModeratedObject = get_moderated_object_model()

        query = Q(community__memberships__user_id=self.pk) & (
                Q(community__memberships__is_moderator=True) | Q(community__memberships__is_administrator=True))

        query.add(Q(status=ModeratedObject.STATUS_PENDING), Q.AND)

        return ModeratedObject.objects.filter(query).count()

    def follow_user(self, user, lists_ids=None):
        return self.follow_user_with_id(user.pk, lists_ids)

    def follow_user_with_id(self, user_id, lists_ids=None):
        check_can_follow_user_with_id(user=self, user_id=user_id)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot follow itself.'),
            )

        if not lists_ids:
            lists_ids = self._get_default_follow_lists()

        check_follow_lists_ids(user=self, lists_ids=lists_ids)

        Follow = get_follow_model()
        follow = Follow.create_follow(user_id=self.pk, followed_user_id=user_id, lists_ids=lists_ids)
        self._create_follow_notification(followed_user_id=user_id)
        self._send_follow_push_notification(followed_user_id=user_id)

        return follow

    def unfollow_user(self, user):
        return self.unfollow_user_with_id(user.pk)

    def unfollow_user_with_id(self, user_id):
        check_is_following_user_with_id(user=self, user_id=user_id)
        follow = self.follows.get(followed_user_id=user_id)
        self._delete_follow_notification(followed_user_id=user_id)
        follow.delete()

    def update_follow_for_user(self, user, lists_ids=None):
        return self.update_follow_for_user_with_id(user.pk, lists_ids=lists_ids)

    def update_follow_for_user_with_id(self, user_id, lists_ids=None):
        check_is_following_user_with_id(user=self, user_id=user_id)

        if not lists_ids:
            lists_ids = self._get_default_follow_lists()

        check_follow_lists_ids(user=self, lists_ids=lists_ids)

        follow = self.get_follow_for_user_with_id(user_id)

        follow.lists.clear()
        follow.lists.add(*lists_ids)
        follow.save()

        return follow

    def remove_list_with_id_from_follow_for_user_with_id(self, user_id, list_id):
        check_is_following_user_with_id(user=self, user_id=user_id)
        check_is_following_user_with_id_in_list_with_id(user=self, user_id=user_id, list_id=list_id)
        follow = self.get_follow_for_user_with_id(user_id)
        follow.lists.remove(list_id)
        return follow

    def add_list_with_id_to_follow_for_user_with_id(self, user_id, list_id):
        check_is_following_user_with_id(user=self, user_id=user_id)
        check_is_not_following_user_with_id_in_list_with_id(user=self, user_id=user_id, list_id=list_id)
        follow = self.get_follow_for_user_with_id(user_id)
        follow.lists.add(list_id)
        return follow

    def connect_with_user_with_id(self, user_id, circles_ids=None):
        check_can_connect_with_user_with_id(user=self, user_id=user_id)

        if not circles_ids:
            circles_ids = self._get_default_connection_circles()
        elif self.connections_circle_id not in circles_ids:
            circles_ids.append(self.connections_circle_id)

        check_connection_circles_ids(user=self, circles_ids=circles_ids)

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
        check_is_not_fully_connected_with_user_with_id(user=self, user_id=user_id)

        if not circles_ids:
            circles_ids = self._get_default_connection_circles()
        elif self.connections_circle_id not in circles_ids:
            circles_ids.append(self.connections_circle_id)

        check_connection_circles_ids(user=self, circles_ids=circles_ids)
        connection = self.update_connection_with_user_with_id(user_id, circles_ids=circles_ids)

        # Automatically follow user
        if not self.is_following_user_with_id(user_id):
            self.follow_user_with_id(user_id)

        self._create_connection_confirmed_notification(user_connected_with_id=user_id)

        return connection

    def update_connection_with_user_with_id(self, user_id, circles_ids=None):
        check_is_connected_with_user_with_id(user=self, user_id=user_id)

        if not circles_ids:
            raise ValidationError(
                _('No data to update the connection with.'),
            )
        elif self.connections_circle_id not in circles_ids:
            circles_ids.append(self.connections_circle_id)

        check_connection_circles_ids(user=self, circles_ids=circles_ids)

        connection = self.get_connection_for_user_with_id(user_id)
        connection.circles.clear()
        connection.circles.add(*circles_ids)
        connection.save()

        return connection

    def disconnect_from_user(self, user):
        return self.disconnect_from_user_with_id(user.pk)

    def disconnect_from_user_with_id(self, user_id):
        check_is_connected_with_user_with_id(user=self, user_id=user_id)
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

    def get_notifications(self, max_id=None, types=None):
        notifications_query = Q()

        if max_id:
            notifications_query.add(Q(id__lt=max_id), Q.AND)

        if types:
            notifications_query.add(Q(notification_type__in=types), Q.AND)

        return self.notifications.filter(notifications_query)

    def read_notifications(self, max_id=None, types=None):
        notifications_query = Q(read=False)

        if max_id:
            notifications_query.add(Q(id__lte=max_id), Q.AND)
        if types:
            notifications_query.add(Q(notification_type__in=types), Q.AND)

        self.notifications.filter(notifications_query).update(read=True)

    def get_unread_notifications(self, max_id=None, types=None):
        notifications_query = Q(read=False)

        if max_id:
            notifications_query.add(Q(id__lte=max_id), Q.AND)
        if types:
            notifications_query.add(Q(notification_type__in=types), Q.AND)

        return self.notifications.filter(notifications_query)

    def read_notification_with_id(self, notification_id):
        check_can_read_notification_with_id(user=self, notification_id=notification_id)
        notification = self.notifications.get(id=notification_id)
        notification.read = True
        notification.save()
        return notification

    def delete_notification_with_id(self, notification_id):
        check_can_delete_notification_with_id(user=self, notification_id=notification_id)
        notification = self.notifications.get(id=notification_id)
        notification.delete()

    def delete_notifications(self):
        self.notifications.all().delete()

    def create_device(self, uuid, name=None):
        check_device_with_uuid_does_not_exist(user=self, device_uuid=uuid)
        Device = get_device_model()
        return Device.create_device(owner=self, uuid=uuid, name=name)

    def update_device_with_uuid(self, device_uuid, name=None):
        check_can_update_device_with_uuid(user=self, device_uuid=device_uuid)
        device = self.devices.get(uuid=device_uuid)
        device.update(name=name)

    def delete_device_with_uuid(self, device_uuid):
        check_can_delete_device_with_uuid(user=self, device_uuid=device_uuid)
        device = self.devices.get(uuid=device_uuid)
        device.delete()

    def get_devices(self, max_id=None):
        devices_query = Q()

        if max_id:
            devices_query.add(Q(id__lt=max_id), Q.AND)

        return self.devices.filter(devices_query)

    def get_device_with_uuid(self, device_uuid):
        check_can_get_device_with_uuid(user=self, device_uuid=device_uuid)
        return self.devices.get(uuid=device_uuid)

    def delete_devices(self):
        self.devices.all().delete()

    def mute_post_with_id(self, post_id):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)
        return self.mute_post(post=post)

    def mute_post(self, post):
        check_can_mute_post(user=self, post=post)
        PostMute = get_post_mute_model()
        PostMute.create_post_mute(post_id=post.pk, muter_id=self.pk)
        return post

    def unmute_post_with_id(self, post_id):
        Post = get_post_model()
        post = Post.objects.get(pk=post_id)

        check_can_unmute_post(user=self, post=post)
        self.post_mutes.filter(post_id=post_id).delete()
        return post

    def mute_post_comment_with_id(self, post_comment_id):
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        return self.mute_post_comment(post_comment=post_comment)

    def mute_post_comment(self, post_comment):
        check_can_mute_post_comment(user=self, post_comment=post_comment)
        PostCommentMute = get_post_comment_mute_model()
        PostCommentMute.create_post_comment_mute(post_comment_id=post_comment.pk, muter_id=self.pk)
        return post_comment

    def unmute_post_comment_with_id(self, post_comment_id):
        Post_comment = get_post_comment_model()
        post_comment = Post_comment.objects.get(pk=post_comment_id)

        check_can_unmute_post_comment(user=self, post_comment=post_comment)
        self.post_comment_mutes.filter(post_comment_id=post_comment_id).delete()
        return post_comment

    def translate_post_comment_with_id(self, post_comment_id):
        check_can_translate_comment_with_id(user=self, post_comment_id=post_comment_id)
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(pk=post_comment_id)
        result = translation_strategy.translate_text(
            source_language_code=post_comment.language.code,
            target_language_code=self.translation_language.code,
            text=post_comment.text
        )
        return post_comment, result.get('translated_text')

    def block_user_with_username(self, username):
        user = User.objects.get(username=username)
        return self.block_user_with_id(user_id=user.pk)

    def block_user_with_id(self, user_id):
        check_can_block_user_with_id(user=self, user_id=user_id)

        if self.is_connected_with_user_with_id(user_id=user_id):
            # This does unfollow too
            self.disconnect_from_user_with_id(user_id=user_id)
        elif self.is_following_user_with_id(user_id=user_id):
            self.unfollow_user_with_id(user_id=user_id)

        user_to_block = User.objects.get(pk=user_id)
        if user_to_block.is_following_user_with_id(user_id=self.pk):
            user_to_block.unfollow_user_with_id(self.pk)

        UserBlock = get_user_block_model()
        UserBlock.create_user_block(blocker_id=self.pk, blocked_user_id=user_id)

        return user_to_block

    def unblock_user_with_username(self, username):
        user = User.objects.get(username=username)
        return self.unblock_user_with_id(user_id=user.pk)

    def unblock_user_with_id(self, user_id):
        check_can_unblock_user_with_id(user=self, user_id=user_id)
        self.user_blocks.filter(blocked_user_id=user_id).delete()
        return User.objects.get(pk=user_id)

    def report_comment_with_id_for_post_with_uuid(self, post_comment_id, post_uuid, category_id, description=None):
        PostComment = get_post_comment_model()
        post_comment = PostComment.objects.get(id=post_comment_id)

        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)

        return self.report_comment_for_post(post_comment=post_comment, category_id=category_id, description=description,
                                            post=post)

    def report_comment_for_post(self, post_comment, post, category_id, description=None):
        check_can_report_comment_for_post(user=self, post_comment=post_comment, post=post)
        ModerationReport = get_moderation_report_model()
        ModerationReport.create_post_comment_moderation_report(post_comment=post_comment,
                                                               category_id=category_id,
                                                               reporter_id=self.pk,
                                                               description=description)
        post_comment.delete_notifications_for_user(user=self)

    def report_post_with_uuid(self, post_uuid, category_id, description=None):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.report_post(post=post, category_id=category_id, description=description)

    def report_post(self, post, category_id, description=None):
        check_can_report_post(user=self, post=post)
        ModerationReport = get_moderation_report_model()
        ModerationReport.create_post_moderation_report(post=post,
                                                       category_id=category_id,
                                                       reporter_id=self.pk,
                                                       description=description)
        post.delete_notifications_for_user(user=self)

    def report_user_with_username(self, username, category_id, description=None):
        user = User.objects.get(username=username)
        return self.report_user(user=user, category_id=category_id, description=description)

    def report_user(self, user, category_id, description=None):
        check_can_report_user(user=self, user_to_report=user)
        ModerationReport = get_moderation_report_model()
        ModerationReport.create_user_moderation_report(user=user,
                                                       category_id=category_id,
                                                       reporter_id=self.pk,
                                                       description=description)

    def report_community_with_name(self, community_name, category_id, description=None):
        Community = get_community_model()
        community = Community.objects.get(name=community_name)
        return self.report_community(community=community, category_id=category_id, description=description)

    def report_community(self, community, category_id, description=None):
        check_can_report_community(user=self, community=community)
        ModerationReport = get_moderation_report_model()
        ModerationReport.create_community_moderation_report(community=community,
                                                            category_id=category_id,
                                                            reporter_id=self.pk,
                                                            description=description)

    def create_invite(self, nickname):
        check_can_create_invite(user=self, nickname=nickname)
        UserInvite = get_user_invite_model()
        invite = UserInvite.create_invite(nickname=nickname, invited_by=self)
        self.invite_count = F('invite_count') - 1
        self.save()
        return invite

    def update_invite(self, invite_id, nickname):
        check_can_update_invite(user=self, invite_id=invite_id)
        UserInvite = get_user_invite_model()
        invite = UserInvite.objects.get(id=invite_id)
        invite.nickname = nickname
        invite.save()
        return invite

    def get_user_invites(self, status_pending=None):
        invites_query = Q(invited_by=self)
        UserInvite = get_user_invite_model()

        if status_pending is not None:
            invites_query.add(Q(created_user__isnull=status_pending), Q.AND)

        return UserInvite.objects.filter(invites_query)

    def search_user_invites(self, query, status_pending=None):
        invites_query = Q(invited_by=self, nickname__icontains=query)
        UserInvite = get_user_invite_model()

        if status_pending is not None:
            invites_query.add(Q(created_user__isnull=status_pending), Q.AND)

        return UserInvite.objects.filter(invites_query)

    def delete_user_invite_with_id(self, invite_id):
        check_can_delete_invite_with_id(user=self, invite_id=invite_id)
        UserInvite = get_user_invite_model()
        invite = UserInvite.objects.get(id=invite_id)
        self.invite_count = F('invite_count') + 1
        self.save()
        invite.delete()

    def send_invite_to_invite_id_with_email(self, invite_id, email):
        check_can_send_email_invite_to_invite_id(user=self, invite_id=invite_id, email=email)
        UserInvite = get_user_invite_model()
        invite = UserInvite.objects.get(id=invite_id)
        invite.email = email
        invite.send_invite_email()

    def verify_moderated_object_with_id(self, moderated_object_id):
        ModeratedObject = get_moderated_object_model()
        moderated_object = ModeratedObject.objects.get(pk=moderated_object_id)
        return self.verify_moderated_object(moderated_object=moderated_object)

    def verify_moderated_object(self, moderated_object):
        check_can_verify_moderated_object(user=self, moderated_object=moderated_object)
        moderated_object.verify_with_actor_with_id(actor_id=self.pk)

    def unverify_moderated_object_with_id(self, moderated_object_id):
        ModeratedObject = get_moderated_object_model()
        moderated_object = ModeratedObject.objects.get(pk=moderated_object_id)
        return self.unverify_moderated_object(moderated_object=moderated_object)

    def unverify_moderated_object(self, moderated_object):
        check_can_unverify_moderated_object(user=self, moderated_object=moderated_object)
        moderated_object.unverify_with_actor_with_id(actor_id=self.pk)

    def approve_moderated_object_with_id(self, moderated_object_id):
        ModeratedObject = get_moderated_object_model()
        moderated_object = ModeratedObject.objects.get(pk=moderated_object_id)
        return self.approve_moderated_object(moderated_object=moderated_object)

    def approve_moderated_object(self, moderated_object):
        check_can_approve_moderated_object(user=self, moderated_object=moderated_object)
        moderated_object.approve_with_actor_with_id(actor_id=self.pk)

    def reject_moderated_object_with_id(self, moderated_object_id):
        ModeratedObject = get_moderated_object_model()
        moderated_object = ModeratedObject.objects.get(pk=moderated_object_id)
        return self.reject_moderated_object(moderated_object=moderated_object)

    def reject_moderated_object(self, moderated_object):
        check_can_reject_moderated_object(user=self, moderated_object=moderated_object)
        moderated_object.reject_with_actor_with_id(actor_id=self.pk)

    def update_moderated_object_with_id(self, moderated_object_id, description=None,
                                        category_id=None):
        ModeratedObject = get_moderated_object_model()
        moderated_object = ModeratedObject.objects.get(pk=moderated_object_id)

        return self.update_moderated_object(moderated_object=moderated_object, description=description,
                                            category_id=category_id)

    def update_moderated_object(self, moderated_object, description=None,
                                category_id=None):
        check_can_update_moderated_object(user=self, moderated_object=moderated_object)
        moderated_object.update_with_actor_with_id(actor_id=self.pk, description=description,
                                                   category_id=category_id)
        return moderated_object

    def search_participants_for_post_with_uuid(self, post_uuid, query):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.search_participants_for_post(post=post, query=query)

    def search_participants_for_post(self, post, query):
        self.can_see_post(post=post)
        # In the future this should prioritise post participants above the global search
        # ATM combining the post participants and global query results in killing perf
        # Therefore for now uses the global search
        search_users_query = self._make_search_users_query(query=query)

        return User.objects.filter(search_users_query)

    def get_participants_for_post_with_uuid(self, post_uuid):
        Post = get_post_model()
        post = Post.objects.get(uuid=post_uuid)
        return self.get_participants_for_post(post=post)

    def get_participants_for_post(self, post):
        self.can_see_post(post=post)
        return post.get_participants()

    def _generate_password_reset_link(self, token):
        return '{0}/api/auth/password/verify?token={1}'.format(settings.EMAIL_HOST, token)

    def _send_password_reset_email_with_token(self, password_reset_token):
        mail_subject = _('Reset your password for Okuna')
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
        helpers.send_post_comment_push_notification_with_message(post_comment=post_comment,
                                                                 message=notification_message,
                                                                 target_user=notification_target_user)

    def _delete_post_comment_notification(self, post_comment):
        if post_comment.parent_comment is not None:
            PostCommentNotification = get_post_comment_notification_model()
            PostCommentNotification.delete_post_comment_notification(post_comment_id=post_comment.pk,
                                                                     owner_id=post_comment.post.creator_id)
        else:
            # Comment is a reply
            self._delete_post_comment_reply_notification(post_comment=post_comment)

    def _delete_post_comment_reply_notification(self, post_comment):
        PostCommentReplyNotification = get_post_comment_notification_model()
        PostCommentReplyNotification.delete_post_comment_notification(post_comment_id=post_comment.pk,
                                                                      owner_id=post_comment.post.creator_id)

    def _create_post_reaction_notification(self, post_reaction):
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.create_post_reaction_notification(post_reaction_id=post_reaction.pk,
                                                                   owner_id=post_reaction.post.creator_id)

    def _send_post_reaction_push_notification(self, post_reaction):
        helpers.send_post_reaction_push_notification(post_reaction=post_reaction)

    def _delete_post_reaction_notification(self, post_reaction):
        PostReactionNotification = get_post_reaction_notification_model()
        PostReactionNotification.delete_post_reaction_notification(post_reaction_id=post_reaction.pk,
                                                                   owner_id=post_reaction.post.creator_id)

    def _create_post_comment_reaction_notification(self, post_comment_reaction):
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.create_post_comment_reaction_notification(
            post_comment_reaction_id=post_comment_reaction.pk,
            owner_id=post_comment_reaction.post_comment.commenter_id)

    def _send_post_comment_reaction_push_notification(self, post_comment_reaction):
        helpers.send_post_comment_reaction_push_notification(post_comment_reaction=post_comment_reaction)

    def _delete_post_comment_reaction_notification(self, post_comment_reaction):
        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        PostCommentReactionNotification.delete_post_comment_reaction_notification(
            post_comment_reaction_id=post_comment_reaction.pk,
            owner_id=post_comment_reaction.post_comment.commenter_id)

    def _create_community_invite_notification(self, community_invite):
        CommunityInviteNotification = get_community_invite_notification_model()
        CommunityInviteNotification.create_community_invite_notification(community_invite_id=community_invite.pk,
                                                                         owner_id=community_invite.invited_user_id)

    def _send_community_invite_push_notification(self, community_invite):
        helpers.send_community_invite_push_notification(community_invite=community_invite)

    def _create_follow_notification(self, followed_user_id):
        FollowNotification = get_follow_notification_model()
        FollowNotification.create_follow_notification(follower_id=self.pk, owner_id=followed_user_id)

    def _send_follow_push_notification(self, followed_user_id):
        followed_user = User.objects.get(pk=followed_user_id)
        helpers.send_follow_push_notification(followed_user=followed_user, following_user=self)

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
        helpers.send_connection_request_push_notification(
            connection_requester=self,
            connection_requested_for=connection_requested_for)

    def _delete_connection_request_notification_for_user_with_id(self, user_id):
        ConnectionRequestNotification = get_connection_request_notification_model()
        ConnectionRequestNotification.delete_connection_request_notification_for_users_with_ids(user_a_id=self.pk,
                                                                                                user_b_id=user_id)

    def _reset_auth_token(self):
        self.auth_token.delete()
        bootstrap_user_auth_token(user=self)

    def _make_linked_users_query(self):
        # All users which are connected with us and we have accepted by adding
        # them to a circle
        linked_users_query = Q(circles__connections__target_connection__user_id=self.pk,
                               circles__connections__target_connection__circles__isnull=False)

        followers_query = self._make_followers_query()

        # All users following us
        linked_users_query.add(followers_query, Q.OR)

        linked_users_query.add(Q(is_deleted=False), Q.AND)

        return linked_users_query

    def _make_followers_query(self):
        return Q(follows__followed_user_id=self.pk, is_deleted=False)

    def _make_followings_query(self):
        return Q(followers__user_id=self.pk, is_deleted=False)

    def _make_blocked_users_query(self, max_id=None):
        blocked_users_query = Q(blocked_by_users__blocker_id=self.pk, )

        if max_id:
            blocked_users_query.add(Q(id__lt=max_id), Q.AND)

        return blocked_users_query

    def _make_get_post_with_id_query_for_user(self, user, post_id):
        posts_query = self._make_get_posts_query_for_user(user)
        posts_query.add(Q(id=post_id), Q.AND)
        return posts_query

    def _make_get_posts_query_for_user(self, user, max_id=None):

        Post = get_post_model()

        posts_query = Q(creator_id=user.pk, is_deleted=False, status=Post.STATUS_PUBLISHED)

        world_circle_id = self._get_world_circle_id()

        posts_circles_query = Q(circles__id=world_circle_id)

        posts_circles_query.add(Q(circles__connections__target_user_id=self.pk,
                                  circles__connections__target_connection__circles__isnull=False), Q.OR)

        posts_query.add(posts_circles_query, Q.AND)
        posts_query.add(~Q(Q(creator__blocked_by_users__blocker_id=self.pk) | Q(
            creator__user_blocks__blocked_user_id=self.pk)), Q.AND)

        if max_id:
            posts_query.add(Q(id__lt=max_id), Q.AND)

        posts_query.add(~Q(moderated_object__reports__reporter_id=self.pk), Q.AND)

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

    def _can_see_post(self, post):
        post_query = self._make_get_post_with_id_query_for_user(post.creator, post_id=post.pk)

        Post = get_post_model()
        profile_posts = Post.objects.filter(post_query)

        return profile_posts.exists()

    def _can_see_community_post(self, community, post):
        if post.creator_id == self.pk:
            return True

        community_posts_query = self._make_get_community_with_id_posts_query(community=community)

        community_posts_query.add(Q(pk=post.pk), Q.AND)

        Post = get_post_model()
        return Post.objects.filter(community_posts_query).exists()

    def _make_get_reactions_for_post_query(self, post, max_id=None, emoji_id=None):
        reactions_query = Q(post_id=post.pk)

        # If reactions are private, return only own reactions
        if not post.public_reactions:
            reactions_query = Q(reactor_id=self.pk)

        post_community = post.community

        if post_community:
            if not self.is_staff_of_community_with_name(community_name=post_community.name):
                blocked_users_query = ~Q(Q(reactor__blocked_by_users__blocker_id=self.pk) | Q(
                    reactor__user_blocks__blocked_user_id=self.pk))
                blocked_users_query_staff_members = Q(
                    reactor__communities_memberships__community_id=post_community.pk)
                blocked_users_query_staff_members.add(Q(reactor__communities_memberships__is_administrator=True) | Q(
                    reactor__communities_memberships__is_moderator=True), Q.AND)

                blocked_users_query.add(~blocked_users_query_staff_members, Q.AND)
                reactions_query.add(blocked_users_query, Q.AND)
        else:
            blocked_users_query = ~Q(Q(reactor__blocked_by_users__blocker_id=self.pk) | Q(
                reactor__user_blocks__blocked_user_id=self.pk))
            reactions_query.add(blocked_users_query, Q.AND)

        if max_id:
            reactions_query.add(Q(id__lt=max_id), Q.AND)

        if emoji_id:
            reactions_query.add(Q(emoji_id=emoji_id), Q.AND)

        return reactions_query

    def _make_get_reactions_for_post_comment_query(self, post_comment, max_id=None, emoji_id=None):
        reactions_query = Q(post_comment_id=post_comment.pk)

        post_comment_community = post_comment.post.community

        if post_comment_community:
            if not self.is_staff_of_community_with_name(community_name=post_comment_community.name):
                blocked_users_query = ~Q(Q(reactor__blocked_by_users__blocker_id=self.pk) | Q(
                    reactor__user_blocks__blocked_user_id=self.pk))
                blocked_users_query_staff_members = Q(
                    reactor__communities_memberships__community_id=post_comment_community.pk)
                blocked_users_query_staff_members.add(Q(reactor__communities_memberships__is_administrator=True) | Q(
                    reactor__communities_memberships__is_moderator=True), Q.AND)

                blocked_users_query.add(~blocked_users_query_staff_members, Q.AND)
                reactions_query.add(blocked_users_query, Q.AND)
        else:
            blocked_users_query = ~Q(Q(reactor__blocked_by_users__blocker_id=self.pk) | Q(
                reactor__user_blocks__blocked_user_id=self.pk))
            reactions_query.add(blocked_users_query, Q.AND)

        if max_id:
            reactions_query.add(Q(id__lt=max_id), Q.AND)

        if emoji_id:
            reactions_query.add(Q(emoji_id=emoji_id), Q.AND)

        return reactions_query

    def _make_get_post_comment_with_id_query(self, post_comment_id, post, post_comment_parent_id=None):

        post_comments_query = self._make_get_comments_for_post_query(post=post,
                                                                     post_comment_parent_id=post_comment_parent_id)

        post_comment_query = Q(pk=post_comment_id)

        post_comments_query.add(post_comment_query, Q.AND)

        return post_comments_query

    def _make_get_comments_for_post_query(self, post, post_comment_parent_id=None, max_id=None, min_id=None):

        # Comments from the post
        comments_query = Q(post_id=post.pk)

        # If we are retrieving replies, add the parent_comment to the query
        if post_comment_parent_id is None:
            comments_query.add(Q(parent_comment__isnull=True), Q.AND)
        else:
            comments_query.add(Q(parent_comment__id=post_comment_parent_id), Q.AND)

        post_community = post.community

        if post_community:
            if not self.is_staff_of_community_with_name(community_name=post_community.name):
                # Dont retrieve posts of blocked users, except from staff members
                blocked_users_query = ~Q(Q(commenter__blocked_by_users__blocker_id=self.pk) | Q(
                    commenter__user_blocks__blocked_user_id=self.pk))
                blocked_users_query_staff_members = Q(
                    commenter__communities_memberships__community_id=post_community.pk)
                blocked_users_query_staff_members.add(Q(commenter__communities_memberships__is_administrator=True) | Q(
                    commenter__communities_memberships__is_moderator=True), Q.AND)

                blocked_users_query.add(~blocked_users_query_staff_members, Q.AND)
                comments_query.add(blocked_users_query, Q.AND)

                # Don't retrieve items that have been reported and approved
                ModeratedObject = get_moderated_object_model()
                comments_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)
        else:
            #  Dont retrieve posts of blocked users
            blocked_users_query = ~Q(Q(commenter__blocked_by_users__blocker_id=self.pk) | Q(
                commenter__user_blocks__blocked_user_id=self.pk))
            comments_query.add(blocked_users_query, Q.AND)

        # Cursor based scrolling queries
        if max_id:
            comments_query.add(Q(id__lt=max_id), Q.AND)
        elif min_id:
            comments_query.add(Q(id__gte=min_id), Q.AND)

        # Dont retrieve items we have reported
        comments_query.add(~Q(moderated_object__reports__reporter_id=self.pk), Q.AND)

        # Dont retrieve soft deleted post comments
        comments_query.add(Q(is_deleted=False), Q.AND)

        return comments_query

    def _make_get_community_with_id_posts_query(self, community, include_closed_posts_for_staff=True):

        Post = get_post_model()

        # Retrieve posts from the given community name
        community_posts_query = Q(community_id=community.pk, is_deleted=False, status=Post.STATUS_PUBLISHED)

        # Don't retrieve items that have been reported and approved
        ModeratedObject = get_moderated_object_model()
        community_posts_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

        # Dont retrieve items we have reported
        community_posts_query.add(~Q(moderated_object__reports__reporter_id=self.pk), Q.AND)

        # Only retrieve posts if we're not banned
        community_posts_query.add(~Q(community__banned_users__id=self.pk), Q.AND)

        # Ensure public/private visibility is respected
        community_posts_visibility_query = Q(community__memberships__user__id=self.pk)
        Community = get_community_model()
        community_posts_visibility_query.add(Q(community__type=Community.COMMUNITY_TYPE_PUBLIC, ), Q.OR)

        community_posts_query.add(community_posts_visibility_query, Q.AND)

        if not self.is_staff_of_community_with_name(community_name=community.name):
            # Dont retrieve closed posts
            community_posts_query.add(Q(is_closed=False) | Q(creator_id=self.pk), Q.AND)

            # Don't retrieve posts of blocked users, except if they're staff members
            blocked_users_query = ~Q(Q(creator__blocked_by_users__blocker_id=self.pk) | Q(
                creator__user_blocks__blocked_user_id=self.pk))

            blocked_users_query_staff_members = Q(creator__communities_memberships__community_id=community)
            blocked_users_query_staff_members.add(Q(creator__communities_memberships__is_administrator=True) | Q(
                creator__communities_memberships__is_moderator=True), Q.AND)

            blocked_users_query.add(~blocked_users_query_staff_members, Q.AND)

            community_posts_query.add(blocked_users_query, Q.AND)
        else:
            if not include_closed_posts_for_staff:
                community_posts_query.add(Q(is_closed=False), Q.AND)

        return community_posts_query


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
                            db_index=True,
                            validators=[name_characters_validator])
    location = models.CharField(_('location'), max_length=settings.PROFILE_LOCATION_MAX_LENGTH, blank=False, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    is_of_legal_age = models.BooleanField(default=False)
    avatar = ProcessedImageField(verbose_name=_('avatar'), blank=False, null=True, format='JPEG',
                                 options={'quality': 90}, processors=[ResizeToFill(500, 500)],
                                 upload_to=upload_to_user_avatar_directory)
    cover = ProcessedImageField(verbose_name=_('cover'), blank=False, null=True, format='JPEG', options={'quality': 90},
                                upload_to=upload_to_user_cover_directory,
                                processors=[ResizeToFit(width=1024, upscale=False)])
    bio = models.TextField(_('bio'), max_length=settings.PROFILE_BIO_MAX_LENGTH, blank=False, null=True)
    url = models.URLField(_('url'), blank=False, null=True)
    followers_count_visible = models.BooleanField(_('followers count visible'), blank=False, null=False, default=False)
    community_posts_visible = models.BooleanField(_('community posts visible'), blank=False, null=False, default=True)
    badges = models.ManyToManyField(Badge, related_name='users_profiles')

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('users profiles')

        index_together = [
            ('id', 'user'),
        ]

    def __repr__(self):
        return '<UserProfile %s>' % self.user.username

    def __str__(self):
        return self.user.username


class UserNotificationsSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='notifications_settings')
    post_comment_notifications = models.BooleanField(_('post comment notifications'), default=True)
    post_comment_reply_notifications = models.BooleanField(_('post comment reply notifications'), default=True)
    post_reaction_notifications = models.BooleanField(_('post reaction notifications'), default=True)
    follow_notifications = models.BooleanField(_('follow notifications'), default=True)
    connection_request_notifications = models.BooleanField(_('connection request notifications'), default=True)
    connection_confirmed_notifications = models.BooleanField(_('connection confirmed notifications'), default=True)
    community_invite_notifications = models.BooleanField(_('community invite notifications'), default=True)
    post_comment_reaction_notifications = models.BooleanField(_('post comment reaction notifications'), default=True)
    post_comment_user_mention_notifications = models.BooleanField(_('post comment user mention notifications'),
                                                                  default=True)
    post_user_mention_notifications = models.BooleanField(_('post user mention notifications'), default=True)

    @classmethod
    def create_notifications_settings(cls, user):
        return UserNotificationsSettings.objects.create(user=user)

    def update(self, post_comment_notifications=None,
               post_comment_reply_notifications=None,
               post_reaction_notifications=None,
               follow_notifications=None,
               connection_request_notifications=None,
               connection_confirmed_notifications=None,
               community_invite_notifications=None,
               post_comment_user_mention_notifications=None,
               post_user_mention_notifications=None,
               post_comment_reaction_notifications=None, ):

        if post_comment_notifications is not None:
            self.post_comment_notifications = post_comment_notifications

        if post_comment_user_mention_notifications is not None:
            self.post_comment_user_mention_notifications = post_comment_user_mention_notifications

        if post_user_mention_notifications is not None:
            self.post_user_mention_notifications = post_user_mention_notifications

        if post_comment_reaction_notifications is not None:
            self.post_comment_reaction_notifications = post_comment_reaction_notifications

        if post_comment_reply_notifications is not None:
            self.post_comment_reply_notifications = post_comment_reply_notifications

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


class UserBlock(models.Model):
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by_users')
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_blocks')

    class Meta:
        unique_together = ('blocked_user', 'blocker',)
        indexes = [
            models.Index(fields=['blocked_user', 'blocker']),
        ]

    @classmethod
    def create_user_block(cls, blocker_id, blocked_user_id):
        return cls.objects.create(blocker_id=blocker_id, blocked_user_id=blocked_user_id)

    @classmethod
    def users_are_blocked(cls, user_a_id, user_b_id):
        return cls.objects.filter(Q(blocked_user_id=user_a_id, blocker_id=user_b_id) | Q(blocked_user_id=user_b_id,
                                                                                         blocker_id=user_a_id)).exists()


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
