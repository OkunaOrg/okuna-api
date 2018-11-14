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
from openbook_common.utils.model_loaders import get_connection_model, get_circle_model, get_follow_model, \
    get_post_model, get_list_model, get_post_comment_model


class User(AbstractUser):
    """"
    Custom user model to change behaviour of the default user model
    such as validation and required fields.
    """
    first_name = None
    last_name = None
    email = models.EmailField(_('email address'), unique=True, null=False, blank=False)
    world_circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.PROTECT, related_name='+', null=True,
                                     blank=True)
    connections_circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.PROTECT, related_name='+',
                                           null=True, blank=True)

    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()

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
    def is_username_taken(cls, username):
        try:
            cls.objects.get(username=username)
            return True
        except User.DoesNotExist:
            return False

    @classmethod
    def is_email_taken(cls, email):
        try:
            cls.objects.get(email=email)
            return True
        except User.DoesNotExist:
            return False

    @property
    def posts_count(self):
        return self.posts.count()

    @property
    def followers_count(self):
        return self.follows.count()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(User, self).save(*args, **kwargs)

    def is_fully_connected_with_user_with_id(self, user_id):
        if not self.is_connected_with_user_with_id(user_id):
            return False

        connection = self.connections.select_related('target_connection__circle').filter(
            target_connection__user_id=user_id).get()
        target_connection = connection.target_connection

        if target_connection.circle and connection.circle:
            return True

        return False

    def is_connected_with_user(self, user):
        return self.is_connected_with_user_with_id(user.pk)

    def is_connected_with_user_with_id(self, user_id):
        count = self.connections.select_related('target_connection__user_id').filter(
            target_connection__user_id=user_id).count()
        return count > 0

    def is_connected_with_user_in_circle(self, user, circle):
        return self.is_connected_with_user_with_id_in_circle_with_id(user.pk, circle.pk)

    def is_connected_with_user_with_id_in_circle_with_id(self, user_id, circle_id):
        return self.connections.select_related('target_connection__user_id').filter(
            target_connection__user_id=user_id,
            circle_id=circle_id).count() == 1

    def is_connected_with_user_in_circles(self, user, circles):
        circles_ids = [circle.pk for circle in circles]
        return self.is_connected_with_user_with_id_in_circles_with_ids(user.pk, circles_ids)

    def is_connected_with_user_with_id_in_circles_with_ids(self, user_id, circles_ids):
        count = self.connections.select_related('target_connection__user_id').filter(
            target_connection__user_id=user_id,
            circle_id__in=circles_ids).count()
        return count > 0

    def is_following_user(self, user):
        return self.is_following_user_with_id(user.pk)

    def is_following_user_with_id(self, user_id):
        return self.follows.filter(followed_user_id=user_id)

    def is_following_user_in_list(self, user, list):
        return self.is_following_user_with_id_in_list_with_id(user.pk, list.pk)

    def is_following_user_with_id_in_list_with_id(self, user_id, list_id):
        return self.follows.filter(
            followed_user_id=user_id,
            list_id=list_id).count() == 1

    def is_world_circle_id(self, id):
        return self.world_circle_id == id

    def is_connections_circle_id(self, id):
        return self.connections_circle_id == id

    def has_circle_with_id(self, circle_id):
        return self.circles.filter(id=circle_id).count() > 0

    def has_circle_with_name(self, circle_name):
        return self.circles.filter(name=circle_name).count() > 0

    def has_post_with_id(self, post_id):
        return self.posts.filter(id=post_id).count() > 0

    def has_circles_with_ids(self, circles_ids):
        return self.circles.filter(id__in=circles_ids).count() == len(circles_ids)

    def has_list_with_id(self, list_id):
        return self.lists.filter(id=list_id).count() > 0

    def has_list_with_name(self, list_name):
        return self.lists.filter(name=list_name).count() > 0

    def has_lists_with_ids(self, lists_ids):
        return self.lists.filter(id__in=lists_ids).count() == len(lists_ids)

    def get_comments_for_post(self, post, **kwargs):
        return self.get_comments_for_post_with_id(post.pk, **kwargs)

    def get_comments_for_post_with_id(self, post_id, min_id=None):
        self._check_can_get_comments_for_post_with_id(post_id)
        comments_query = Q(post_id=post_id)

        if min_id:
            comments_query.add(Q(id__gt=min_id), Q.AND)

        PostComment = get_post_comment_model()
        return PostComment.objects.filter(comments_query)

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

    def update_circle_with_id(self, circle_id, **kwargs):
        self._check_can_update_circle_with_id(circle_id)
        self._check_circle_data(kwargs)
        circle = self.circles.get(id=circle_id)

        for attr, value in kwargs.items():
            setattr(circle, attr, value)
        circle.save()

    def get_circle_with_id(self, circle_id):
        self._check_can_get_circle_with_id(circle_id)
        return self.circles.get(id=circle_id)

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

    def update_list_with_id(self, list_id, **kwargs):
        self._check_can_update_list_with_id(list_id)
        self._check_list_data(kwargs)
        list = self.lists.get(id=list_id)

        for attr, value in kwargs.items():
            setattr(list, attr, value)
        list.save()

    def get_list_with_id(self, list_id):
        self._check_can_get_list_with_id(list_id)
        return self.lists.get(id=list_id)

    def create_public_post(self, text=None, image=None):
        return self.create_post(text=text, image=image, circle_id=self.world_circle_id)

    def create_post(self, text, circles_ids=None, circles=None, circle=None, circle_id=None, **kwargs):
        if circles:
            circles_ids = [circle.pk for circle in circles]
        elif not circles_ids:
            circles_ids = []
            if circle:
                circle_id = circle.pk

            if circle_id:
                circles_ids.append(circle_id)

        self._check_post_data(kwargs)

        if len(circles_ids) == 0:
            # If no circle, add post to world circle
            circles_ids.append(self.world_circle_id)

        Post = get_post_model()
        post = Post.create_post(text=text, creator=self, circles_ids=circles_ids, **kwargs)

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

    def get_timeline_posts(self, lists_ids=None, circles_ids=None, max_id=None, post_id=None):

        queries = []

        follows = None

        if lists_ids:
            follows = self.follows.filter(list_id__in=lists_ids)
        else:
            follows = self.follows.all()

        for follow in follows:
            followed_user = follow.followed_user

            is_connected_with_followed_user = None

            if circles_ids:
                is_connected_with_followed_user = self.is_connected_with_user_with_id_in_circles_with_ids(followed_user,
                                                                                                          circles_ids)
                if is_connected_with_followed_user:
                    # Add the connected & followed user public posts
                    followed_user_world_circle_query = Q(creator_id=followed_user.pk,
                                                         circles__id=followed_user.world_circle.pk)
                    queries.append(followed_user_world_circle_query)
            else:
                is_connected_with_followed_user = self.is_connected_with_user(followed_user)
                # Add the followed user public posts
                followed_user_world_circle_query = Q(creator_id=followed_user.pk,
                                                     circles__id=followed_user.world_circle.pk)
                queries.append(followed_user_world_circle_query)

            if is_connected_with_followed_user:
                Connection = get_connection_model()

                connection = Connection.objects.select_related(
                    'target_connection__user'
                ).filter(
                    user_id=self.pk,
                    target_connection__user_id=followed_user.pk).get()

                target_connection = connection.target_connection

                # Add the connected user posts with connections circle
                connected_user_connections_circle_posts_query = Q(creator_id=target_connection.user_id,
                                                                  circles__id=target_connection.user.connections_circle.pk)
                queries.append(connected_user_connections_circle_posts_query)

                # Add the connected user circle posts we might be in
                target_connection_circle = connection.target_connection.circle
                # The other user might not have the user in a circle yet
                if target_connection_circle:
                    connected_user_circle_posts_query = Q(creator_id=target_connection.user_id,
                                                          circles__id=target_connection.circle_id)
                    queries.append(connected_user_circle_posts_query)

        final_query = Q(creator_id=self.pk)

        for query in queries:
            final_query.add(query, Q.OR)

        if max_id:
            final_query.add(Q(id__lt=max_id), Q.AND)
        elif post_id:
            final_query.add(Q(id=post_id), Q.AND)

        Post = get_post_model()
        result = Post.objects.filter(final_query)

        return result

    def follow_user(self, user, **kwargs):
        return self.follow_user_with_id(user.pk, **kwargs)

    def follow_user_with_id(self, user_id, **kwargs):
        self._check_is_not_following_user_with_id(user_id)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot follow itself.'),
            )

        self._check_follow_data(kwargs)

        Follow = get_follow_model()
        return Follow.create_follow(user_id=self.pk, followed_user_id=user_id, **kwargs)

    def unfollow_user(self, user):
        return self.unfollow_user_with_id(user.pk)

    def unfollow_user_with_id(self, user_id):
        self._check_is_following_user_with_id(user_id)
        follow = self.follows.get(followed_user_id=user_id)
        follow.delete()

    def update_follow_for_user(self, user, **kwargs):
        return self.update_follow_for_user_with_id(user.pk, **kwargs)

    def update_follow_for_user_with_id(self, user_id, **kwargs):
        self._check_is_following_user_with_id(user_id)
        self._check_follow_data(kwargs)
        follow = self.get_follow_for_user_with_id(user_id)
        for attr, value in kwargs.items():
            setattr(follow, attr, value)
        follow.save()
        return follow

    def connect_with_user_with_id(self, user_id, circle_id=None):
        self._check_is_not_connected_with_user_with_id(user_id)

        if not circle_id:
            circle_id = self.connections_circle_id

        self.check_connection_circle_id(circle_id)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot connect with itself.'),
            )
        Connection = get_connection_model()
        connection = Connection.create_connection(user_id=self.pk, target_user_id=user_id, circle_id=circle_id)
        # Automatically follow user
        if not self.is_following_user_with_id(user_id):
            self.follow_user_with_id(user_id)

        return connection

    def confirm_connection_with_user_with_id(self, user_id, circle_id=None):
        self._check_is_not_fully_connected_with_user_with_id(user_id)

        if not circle_id:
            circle_id = self.connections_circle_id
        self.check_connection_circle_id(circle_id)

        return self.update_connection_with_user_with_id(user_id, circle_id=circle_id)

    def update_connection_with_user_with_id(self, user_id, circle_id=None):
        self._check_is_connected_with_user_with_id(user_id)

        if not circle_id:
            raise ValidationError(
                _('No data to update the connection with.'),
            )

        self.check_connection_circle_id(circle_id)
        connection = self.get_connection_for_user_with_id(user_id)
        connection.circle_id = circle_id
        connection.save()
        return connection

    def check_connection_circle_id(self, circle_id):
        self._check_has_circle_with_id(circle_id)

        if self.is_world_circle_id(circle_id):
            raise ValidationError(
                _('Can\'t connect in the world circle.'),
            )

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

    def get_connection_for_user_with_id(self, user_id):
        return self.connections.get(target_connection__user_id=user_id)

    def get_follow_for_user_with_id(self, user_id):
        return self.follows.get(followed_user_id=user_id)

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

    def _check_can_see_post_with_id(self, post_id):
        # Check if post is public
        Post = get_post_model()
        post = Post.objects.filter(pk=post_id).get()
        if post.is_public_post():
            return

        if self.get_timeline_posts(post_id=post_id).count() == 0:
            raise ValidationError(
                _('This post is private.'),
            )

    def _check_follow_data(self, data):
        list_id = data.get('list_id')

        if not list_id:
            list = data.get('list')
            if list:
                list_id = list.pk

        if list_id:
            self._check_has_list_with_id(list_id)

    def _check_post_data(self, data):
        circles_ids = data.get('circles_ids')

        if circles_ids:
            self._check_has_circles_with_ids(circles_ids)

    def _check_list_data(self, data):
        name = data.get('name')
        if name:
            self._check_list_name_not_taken(name)

    def _check_circle_data(self, data):
        name = data.get('name')
        if name:
            self._check_circle_name_not_taken(name)

    def _check_is_not_following_user_with_id(self, user_id):
        if self.is_following_user_with_id(user_id):
            raise ValidationError(
                _('Already following user.'),
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
    name = models.CharField(_('name'), max_length=50, blank=False, null=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField(_('birth date'), null=False, blank=False)
    avatar = models.ImageField(_('avatar'), blank=True, null=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('users profiles')

    def __repr__(self):
        return '<UserProfile %s>' % self.user.username

    def __str__(self):
        return self.user.username
