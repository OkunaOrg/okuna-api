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

from openbook.settings import USERNAME_MAX_LENGTH
from openbook_common.utils.model_loaders import get_connection_model, get_circle_model, get_follow_model


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

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(User, self).save(*args, **kwargs)

    def is_connected_with_user(self, user):
        return self.is_connected_with_user_with_id(user.pk)

    def is_connected_with_user_with_id(self, user_id):
        count = self.connections.select_related('target_connection__user_id').filter(
            target_connection__user_id=user_id).count()
        return count > 0

    def is_connected_with_user_in_circles(self, user, circles):
        circles_ids = [circle.pk for circle in circles]
        return self.is_connected_with_user_with_id_in_circles_with_ids(user.pk, circles_ids)

    def is_connected_with_user_with_id_in_circles_with_ids(self, user_id, circles_ids):
        count = self.connections.select_related('target_connection__user_id').filter(
            target_connection__user_id=user_id,
            circle_id__in=circles_ids).count()
        return count == len(circles_ids)

    def is_following_user(self, user):
        return self.is_following_user_with_id(user.pk)

    def is_following_user_with_id(self, user_id):
        return self.follows.filter(followed_user_id=user_id)

    def has_circle_with_id(self, circle_id):
        return self.circles.filter(id=circle_id).count() > 0

    def has_circles_with_ids(self, circles_ids):
        return self.circles.filter(id__in=circles_ids).count() == len(circles_ids)

    def has_list_with_id(self, list_id):
        return self.lists.filter(id=list_id).count() > 0

    def has_lists_with_ids(self, lists_ids):
        return self.lists.filter(id__in=lists_ids).count() == len(lists_ids)

    def get_posts(self, lists_ids=None, circles_ids=None):
        # TODO Desperately optimize. Basically the core functionality of everything.
        posts_queryset = self.posts.all()

        follows = None

        if lists_ids:
            follows = self.follows.filter(list_id__in=lists_ids)
        else:
            follows = self.follows.all()

        for follow in follows:
            followed_user = follow.followed_user

            is_connected_with_followed_user = None

            if circles_ids:
                is_connected_with_followed_user = self.is_connected_with_user_in_circles(followed_user, circles_ids)
                if is_connected_with_followed_user:
                    # Add the connected user public posts
                    posts_queryset = posts_queryset | followed_user.world_circle.posts.all()
            else:
                is_connected_with_followed_user = self.is_connected_with_user(followed_user)
                # Add the followed user public posts
                posts_queryset = posts_queryset | followed_user.world_circle.posts.all()

            if is_connected_with_followed_user:
                Connection = get_connection_model()

                connection = Connection.objects.select_related(
                    'target_connection__user'
                ).prefetch_related(
                    'target_connection__user__connections_circle__posts'
                ).filter(
                    user_id=self.pk,
                    target_connection__user_id=followed_user.pk).get()

                target_connection = connection.target_connection

                # Add the connected user posts with connections circle
                posts_queryset = posts_queryset | target_connection.user.connections_circle.posts.all()

                # Add the connected user circle posts we might be in
                target_connection_circle = connection.target_connection.circle
                # The other user might not have the user in a circle yet
                if target_connection_circle:
                    target_connection_circle_posts = target_connection_circle.posts.all()
                    posts_queryset = posts_queryset | target_connection_circle_posts

        return posts_queryset

    def follow_user(self, user, **kwargs):
        return self.follow_user_with_id(user.pk, **kwargs)

    def follow_user_with_id(self, user_id, **kwargs):
        self.check_is_not_following_user_with_id(user_id)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot follow itself.'),
            )

        self.check_follow_data(kwargs)

        Follow = get_follow_model()
        return Follow.create_follow(user_id=self.pk, followed_user_id=user_id, **kwargs)

    def unfollow_user(self, user):
        return self.unfollow_user_with_id(user.pk)

    def unfollow_user_with_id(self, user_id):
        self.check_is_following_user_with_id(user_id)
        follow = self.follows.get(followed_user_id=user_id)
        follow.delete()

    def update_follow_for_user(self, user, **kwargs):
        return self.update_follow_for_user_with_id(user.pk, **kwargs)

    def update_follow_for_user_with_id(self, user_id, **kwargs):
        self.check_is_following_user_with_id(user_id)
        self.check_follow_data(kwargs)
        follow = self.get_follow_for_user_with_id(user_id)
        for attr, value in kwargs.items():
            setattr(follow, attr, value)
        follow.save()
        return follow

    def connect_with_user(self, user, **kwargs):
        return self.connect_with_user_with_id(user.pk, **kwargs)

    def connect_with_user_with_id(self, user_id, **kwargs):
        self.check_is_not_connected_with_user_with_id(user_id)
        self.check_connect_data(kwargs)

        if self.pk == user_id:
            raise ValidationError(
                _('A user cannot follow itself.'),
            )

        Connection = get_connection_model()
        connection = Connection.create_connection(user_id=self.pk, target_user_id=user_id, **kwargs)

        # Automatically follow user
        if not self.is_following_user_with_id(user_id):
            self.follow_user_with_id(user_id)

        return connection

    def update_connection_with_user_with_id(self, user_id, **kwargs):
        self.check_is_connected_with_user_with_id(user_id)
        self.check_connect_data(kwargs)
        connection = self.get_connection_for_user_with_id(user_id)
        for attr, value in kwargs.items():
            setattr(connection, attr, value)
        connection.save()
        return connection

    def check_connect_data(self, data):
        circle_id = data.get('circle_id')

        if not circle_id:
            circle = data.get('circle')
            if circle:
                circle_id = circle.pk

        if circle_id:
            self.check_has_circle_with_id(circle_id)

    def disconnect_from_user(self, user):
        return self.disconnect_from_user_with_id(user.pk)

    def disconnect_from_user_with_id(self, user_id):
        self.check_is_connected_with_user_with_id(user_id)
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

    def check_follow_data(self, data):
        list_id = data.get('list_id')

        if not list_id:
            list = data.get('list')
            if list:
                list_id = list.pk

        if list_id:
            self.check_has_list_with_id(list_id)

    def check_is_not_following_user_with_id(self, user_id):
        if self.is_following_user_with_id(user_id):
            raise ValidationError(
                _('Already following user.'),
            )

    def check_is_following_user_with_id(self, user_id):
        if not self.is_following_user_with_id(user_id):
            raise ValidationError(
                _('Not following user.'),
            )

    def check_is_not_connected_with_user_with_id(self, user_id):
        if self.is_connected_with_user_with_id(user_id):
            raise ValidationError(
                _('Already connected with user.'),
            )

    def check_is_connected_with_user_with_id(self, user_id):
        if not self.is_connected_with_user_with_id(user_id):
            raise ValidationError(
                _('Not connected with user.'),
            )

    def check_has_list_with_id(self, list_id):
        if not self.has_list_with_id(list_id):
            raise ValidationError(
                _('List does not exist.'),
            )

    def check_has_circle_with_id(self, circle_id):
        if not self.has_circle_with_id(circle_id):
            raise ValidationError(
                _('Circle does not exist.'),
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
