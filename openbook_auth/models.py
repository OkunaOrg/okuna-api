import secrets
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.db.models import Q

from openbook.settings import USERNAME_MAX_LENGTH
from openbook_auth.exceptions import EmailVerificationTokenInvalid
from openbook_common.models import Badge
from openbook_common.utils.model_loaders import get_connection_model, get_circle_model, get_follow_model, \
    get_post_model, get_list_model, get_post_comment_model, get_post_reaction_model, \
    get_emoji_group_model, get_user_invite_model, get_community_model, get_community_invite_model
from openbook_common.validators import name_characters_validator


class User(AbstractUser):
    """"
    Custom user model to change behaviour of the default user model
    such as validation and required fields.
    """
    first_name = None
    last_name = None
    email = models.EmailField(_('email address'), unique=True, null=False, blank=False)
    connections_circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.PROTECT, related_name='+',
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

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @classmethod
    def create_user(cls, username, email=None, password=None, name=None, avatar=None, is_of_legal_age=None,
                    **extra_fields):
        new_user = cls.objects.create_user(username, email=email, password=password, **extra_fields)
        UserProfile.objects.create(name=name, user=new_user, avatar=avatar,
                                   is_of_legal_age=is_of_legal_age)
        return new_user

    @classmethod
    def is_username_taken(cls, username):
        UserInvite = get_user_invite_model()
        user_invites = UserInvite.objects.filter(username=username)
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
    def get_temporary_username(cls, email):
        username = email.split('@')[0]
        temp_username = username
        while cls.is_username_taken(temp_username):
            temp_username = username + str(secrets.randbelow(9999))

        return temp_username

    @classmethod
    def get_public_users_with_query(cls, query):
        users_query = Q(username__icontains=query)
        users_query.add(Q(profile__name__icontains=query), Q.OR)
        return cls.objects.filter(users_query)

    def count_posts(self):
        return self.posts.count()

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
        self.profile.cover.delete(save=save)

    def update_profile_avatar(self, avatar, save=True):
        if avatar is None:
            self.delete_profile_avatar(save=False)
        else:
            self.profile.avatar = avatar

        if save:
            self.profile.save()

    def delete_profile_avatar(self, save=True):
        self.profile.avatar.delete(save=save)

    def update_username(self, username):
        self._check_username_not_taken(username)
        self.username = username
        self.save()

    def update_password(self, password):
        self.set_password(password)
        self.save()

    def update_email(self, email):
        self._check_email_not_taken(email)
        self.email = email
        self.is_email_verified = False
        self.save()

    def set_email_verified(self):
        self.is_email_verified = True

    def verify_email_with_token(self, token):
        is_token_valid = PasswordResetTokenGenerator().check_token(self, token)
        if not is_token_valid:
            raise EmailVerificationTokenInvalid()
        self.set_email_verified()

    def make_email_verification_token(self):
        return PasswordResetTokenGenerator().make_token(self)

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
        return self.circles.filter(name=circle_name).count() > 0

    def has_post_with_id(self, post_id):
        return self.posts.filter(id=post_id).count() > 0

    def has_circles_with_ids(self, circles_ids):
        return self.circles.filter(id__in=circles_ids).count() == len(circles_ids)

    def has_list_with_id(self, list_id):
        return self.lists.filter(id=list_id).count() > 0

    def is_administrator_of_community_with_name(self, community_name):
        return self.administrated_communities.filter(name=community_name).exists()

    def is_member_of_community_with_name(self, community_name):
        return self.communities.filter(name=community_name).exists()

    def is_creator_of_community_with_name(self, community_name):
        return self.created_communities.filter(name=community_name).exists()

    def is_moderator_of_community_with_name(self, community_name):
        return self.moderated_communities.filter(name=community_name).exists()

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
        return self.posts_comments.filter(post_id=post_id).count() > 0

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

        return post_reaction

    def delete_reaction_with_id_for_post_with_id(self, post_reaction_id, post_id):
        self._check_can_delete_reaction_with_id_for_post_with_id(post_reaction_id, post_id)
        Post = get_post_model()
        post = Post.objects.filter(pk=post_id).get()
        post.remove_reaction_with_id(post_reaction_id)

    def get_comments_for_post_with_id(self, post_id, max_id=None):
        self._check_can_get_comments_for_post_with_id(post_id)
        comments_query = Q(post_id=post_id)

        Post = get_post_model()

        # If comments are private, return only own comments
        if not Post.post_with_id_has_public_comments(post_id):
            comments_query = Q(commenter_id=self.pk)

        if max_id:
            comments_query.add(Q(id__lt=max_id), Q.AND)

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
        return post_comment

    def delete_comment_with_id_for_post_with_id(self, post_comment_id, post_id):
        self._check_can_delete_comment_with_id_for_post_with_id(post_comment_id, post_id)
        Post = get_post_model()
        post = Post.objects.filter(pk=post_id).get()
        post.remove_comment_with_id(post_comment_id)

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

    def create_community(self, name, title=None, description=None, rules=None,
                         avatar=None, cover=None, type=None, color=None, user_adjective=None, users_adjective=None):
        self._check_community_name_not_taken(name)
        Community = get_community_model()
        community = Community.create_community(name=name, creator=self, title=title, description=description,
                                               rules=rules, cover=cover, type=type, avatar=avatar, color=color,
                                               user_adjective=user_adjective, users_adjective=users_adjective)

        return community

    def delete_community(self, community):
        return self.delete_community_with_name(community.name)

    def delete_community_with_name(self, community_name):
        self._check_can_delete_community_with_name(community_name)
        community = self.administrated_communities.get(name=community_name)
        community.delete()

    def update_community(self, community, title=None, name=None, description=None, color=None, type=None,
                         user_adjective=None,
                         users_adjective=None, rules=None):
        return self.update_community_with_name(community.name, name=name, title=title, description=description,
                                               color=color, type=type, user_adjective=user_adjective,
                                               users_adjective=users_adjective, rules=rules)

    def update_community_with_name(self, community_name, title=None, name=None, description=None, color=None, type=None,
                                   user_adjective=None,
                                   users_adjective=None, rules=None):
        self._check_can_update_community_with_name(community_name)
        self._check_community_data(name)

        community_to_update = self.communities.get(name=community_name)

        if name:
            community_to_update.name = name

        if title:
            community_to_update.title = title

        if type:
            community_to_update.type = type

        if color:
            community_to_update.color = color

        if description is not None:
            community_to_update.description = description

        if rules is not None:
            community_to_update.rules = rules

        if user_adjective is not None:
            community_to_update.user_adjective = user_adjective

        if users_adjective is not None:
            community_to_update.users_adjective = users_adjective

        community_to_update.save()

        return community_to_update

    def update_community_with_name_avatar(self, community_name, avatar):
        self._check_can_update_community_with_name(community_name)
        self._check_community_data(avatar=avatar)

        community_to_update_avatar_from = self.administrated_communities.get(name=community_name)
        community_to_update_avatar_from.avatar = avatar

        community_to_update_avatar_from.save()

        return community_to_update_avatar_from

    def delete_community_with_name_avatar(self, community_name):
        self._check_can_update_community_with_name(community_name)
        community_to_delete_avatar_from = self.administrated_communities.get(name=community_name)
        community_to_delete_avatar_from.avatar.delete()
        return community_to_delete_avatar_from

    def update_community_with_name_cover(self, community_name, cover):
        self._check_can_update_community_with_name(community_name)
        self._check_community_data(cover=cover)

        community_to_update_cover_from = self.administrated_communities.get(name=community_name)
        community_to_update_cover_from.cover = cover

        community_to_update_cover_from.save()

        return community_to_update_cover_from

    def delete_community_with_name_cover(self, community_name):
        self._check_can_update_community_with_name(community_name)
        community_to_delete_cover_from = self.administrated_communities.get(name=community_name)
        community_to_delete_cover_from.cover.delete()
        return community_to_delete_cover_from

    def get_community_with_name_members(self, community_name, max_id):
        self._check_can_get_community_with_name_members(
            community_name=community_name)

        Community = get_community_model()
        return Community.get_community_with_name_members(community_name=community_name, members_max_id=max_id)

    def join_community_with_name(self, community_name):
        self._check_can_join_community_with_name(
            community_name=community_name)
        Community = get_community_model()
        community_to_join = Community.objects.get(name=community_name)
        community_to_join.members.add(self)

        # Clean up any invites
        CommunityInvite = get_community_invite_model()
        CommunityInvite.objects.filter(community__name=community_name, invited_user__username=self.username).delete()

        return community_to_join

    def leave_community_with_name(self, community_name):
        self._check_can_leave_community_with_name(
            community_name=community_name)

        Community = get_community_model()
        community_to_leave = Community.objects.get(name=community_name)

        if self.is_moderator_of_community_with_name(community_name):
            community_to_leave.moderators.remove(self)

        if self.is_administrator_of_community_with_name(community_name):
            community_to_leave.administrators.remove(self)

        community_to_leave.members.remove(self)

        return community_to_leave

    def add_administrator_with_username_to_community_with_name(self, username, community_name):
        self._check_can_add_administrator_with_username_to_community_with_name(
            username=username,
            community_name=community_name)

    def get_community_with_name_administrators(self, community_name, max_id):
        self._check_can_get_community_with_name_administrators(
            community_name=community_name)

    def remove_administrator_with_username_from_community_with_name(self, username, community_name):
        self._check_can_remove_administrator_with_username_to_community_with_name(
            username=username,
            community_name=community_name)

    def get_community_with_name_banned_users(self, community_name, max_id):
        self._check_can_get_community_with_name_banned_users(
            community_name=community_name)

    def ban_user_with_username_from_community_with_name(self, username, community_name):
        self._check_can_ban_user_with_username_from_community_with_name(username=username,
                                                                        community_name=community_name)

    def unban_user_with_username_from_community_with_name(self, username, community_name):
        self._check_can_unban_user_with_username_from_community_with_name(username=username,
                                                                          community_name=community_name)

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

    def get_users_with_query(self, query):
        # In the future, the user might have blocked users which should not be displayed
        return User.get_public_users_with_query(query)

    def get_communities_with_query(self, query):
        # In the future, the user might have blocked communities which should not be displayed
        Community = get_community_model()
        return Community.get_communities_with_query(query)

    def get_community_with_name(self, community_name):
        Community = get_community_model()
        return Community.objects.get(name=community_name)

    def create_public_post(self, text=None, image=None):
        # If no circle ids are given, will be public
        return self.create_post(text=text, image=image)

    def create_encircled_post(self, circles_ids, text=None, image=None):
        return self.create_post(text=text, image=image, circles_ids=circles_ids)

    def create_post(self, text=None, image=None, video=None, circles_ids=None, circles=None, circle=None,
                    circle_id=None, created=None):

        if circles:
            circles_ids = [circle.pk for circle in circles]
        elif not circles_ids:
            circles_ids = []
            if circle:
                circle_id = circle.pk

            if circle_id:
                circles_ids.append(circle_id)

        self._check_post_data(circles_ids=circles_ids)

        if len(circles_ids) == 0:
            # If no circle, add post to world circle
            world_circle_id = self._get_world_circle_id()
            circles_ids.append(world_circle_id)

        Post = get_post_model()
        post = Post.create_post(text=text, creator=self, circles_ids=circles_ids, image=image, video=video,
                                created=created)

        return post

    def delete_post(self, post):
        return self.delete_post_with_id(post.pk)

    def delete_post_with_id(self, post_id):
        self._check_can_delete_post_with_id(post_id)
        post = self.posts.get(id=post_id)
        post.delete()

    def update_post(self, post):
        return self.update_post_with_id(post.pk)

    def update_post_with_id(self, post_id):
        pass

    def get_post_with_id_for_user_with_username(self, username, post_id):
        user = User.objects.get(username=username)
        return self.get_post_with_id_for_user(user, post_id=post_id)

    def get_post_with_id_for_user(self, user, post_id):
        post_query = self._make_get_post_with_id_query_for_user(user, post_id=post_id)

        Post = get_post_model()
        profile_posts = Post.objects.filter(post_query)

        return profile_posts

    def get_posts(self, max_id=None):
        """
        Get all the posts for ourselves
        :param max_id:
        :return:
        """
        posts_query = Q(creator_id=self.id)

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
        :param lists_ids:
        :param circles_ids:
        :param max_id:
        :param post_id:
        :param username:
        :return:
        """
        # Add all own posts
        if circles_ids or lists_ids:
            timeline_posts_query = Q()
        else:
            timeline_posts_query = Q(creator_id=self.pk)

        follows_related_query = self.follows.select_related('followed_user')

        if lists_ids:
            follows = follows_related_query.filter(lists__id__in=lists_ids)
        else:
            follows = follows_related_query.all()

        for follow in follows:
            followed_user = follow.followed_user
            if circles_ids:
                # Check that the user belongs to the filtered circles
                if self.is_connected_with_user_with_id_in_circles_with_ids(followed_user.pk, circles_ids):
                    followed_user_posts_query = self._make_get_posts_query_for_user(followed_user, )
                    timeline_posts_query.add(followed_user_posts_query, Q.OR)
            else:
                followed_user_posts_query = self._make_get_posts_query_for_user(followed_user, )
                timeline_posts_query.add(followed_user_posts_query, Q.OR)

        if max_id:
            timeline_posts_query.add(Q(id__lt=max_id), Q.AND)

        Post = get_post_model()
        timeline_posts = Post.objects.filter(timeline_posts_query).distinct()

        return timeline_posts

    def follow_user(self, user, lists_ids=None):
        return self.follow_user_with_id(user.pk, lists_ids)

    def follow_user_with_id(self, user_id, lists_ids=None):
        self._check_is_not_following_user_with_id(user_id)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot follow itself.'),
            )

        if not lists_ids:
            lists_ids = self._get_default_follow_lists()

        self._check_follow_lists_ids(lists_ids)

        Follow = get_follow_model()
        return Follow.create_follow(user_id=self.pk, followed_user_id=user_id, lists_ids=lists_ids)

    def unfollow_user(self, user):
        return self.unfollow_user_with_id(user.pk)

    def unfollow_user_with_id(self, user_id):
        self._check_is_following_user_with_id(user_id)
        follow = self.follows.get(followed_user_id=user_id)
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
        # Actually disconnect
        connection = self.connections.get(target_connection__user_id=user_id)
        connection.delete()
        # Stop following user
        if self.is_following_user_with_id(user_id):
            self.unfollow_user_with_id(user_id)

        return connection

    def get_connection_for_user_with_id(self, user_id):
        return self.connections.get(target_connection__user_id=user_id)

    def get_follow_for_user_with_id(self, user_id):
        return self.follows.get(followed_user_id=user_id)

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

    def _check_can_delete_comment_with_id_for_post_with_id(self, post_comment_id, post_id):
        # Check if the post belongs to us
        if self.has_post_with_id(post_id):
            # Check that the comment belongs to the post
            PostComment = get_post_comment_model()
            if PostComment.objects.filter(id=post_comment_id, post_id=post_id).count() == 0:
                raise ValidationError(
                    _('That comment does not belong to the specified post.')
                )
            return

        if self.posts_comments.filter(id=post_comment_id).count() == 0:
            raise ValidationError(
                _('Can\'t delete a comment that does not belong to you.'),
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

        post_creator = post.creator

        # Check if we can retrieve the post
        if not self.get_post_with_id_for_user(post_id=post_id, user=post_creator).exists():
            raise ValidationError(
                _('This post is private.'),
            )

    def _check_follow_lists_ids(self, lists_ids):
        for list_id in lists_ids:
            self._check_follow_list_id(list_id)

    def _check_follow_list_id(self, list_id):
        self._check_has_list_with_id(list_id)

    def _check_post_data(self, circles_ids=None):

        if circles_ids:
            self._check_has_circles_with_ids(circles_ids)

    def _check_list_data(self, name, emoji_id):
        if name:
            self._check_list_name_not_taken(name)

    def _check_community_data(self, name=None, avatar=None, cover=None):
        if name:
            self._check_community_name_not_taken(name)

    def _check_circle_data(self, name, color):
        if name:
            self._check_circle_name_not_taken(name)

    def _check_is_not_following_user_with_id(self, user_id):
        if self.is_following_user_with_id(user_id):
            raise ValidationError(
                _('Already following user.'),
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
        if not self.has_post_with_id(post_id):
            raise ValidationError(
                _('Can\'t delete a post that does not belong to you.'),
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

    def _check_can_get_community_with_name_members(self, community_name):
        Community = get_community_model()

        if Community.is_community_with_name_private(community_name=community_name):
            if not self.is_member_of_community_with_name(community_name=community_name):
                raise ValidationError(
                    _('Can\'t see the members of a private community.'),
                )

    def _check_can_join_community_with_name(self, community_name):
        if self.is_member_of_community_with_name(community_name):
            raise ValidationError(
                _('You are already a member of the community.'),
            )

        Community = get_community_model()
        if Community.is_community_with_name_private(community_name=community_name):
            if not Community.is_user_with_username_invited_to_community_with_name(username=self.username,
                                                                                  community_name=community_name):
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

    def _check_community_name_not_taken(self, community_name):
        Community = get_community_model()
        if Community.is_name_taken(community_name):
            raise ValidationError(
                _('A community with that name already exists.'),
            )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """"
    Create a token for all users
    """
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def bootstrap_circles(sender, instance=None, created=False, **kwargs):
    """"
    Bootstrap the user circles
    """
    if created:
        Circle = get_circle_model()
        Circle.bootstrap_circles_for_user(instance)


class UserProfile(models.Model):
    name = models.CharField(_('name'), max_length=settings.PROFILE_NAME_MAX_LENGTH, blank=False, null=False,
                            validators=[name_characters_validator])
    location = models.CharField(_('location'), max_length=settings.PROFILE_LOCATION_MAX_LENGTH, blank=False, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    is_of_legal_age = models.BooleanField(default=False)
    avatar = models.ImageField(_('avatar'), blank=False, null=True)
    cover = models.ImageField(_('cover'), blank=False, null=True)
    bio = models.CharField(_('bio'), max_length=settings.PROFILE_BIO_MAX_LENGTH, blank=False, null=True)
    url = models.URLField(_('url'), blank=False, null=True)
    followers_count_visible = models.BooleanField(_('followers count visible'), blank=False, null=False, default=False)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('users profiles')

    def __repr__(self):
        return '<UserProfile %s>' % self.user.username

    def __str__(self):
        return self.user.username


class UserProfileBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
