from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    """"
    Custom user model to change behaviour of the default user model
    such as validation and required fields.
    """
    first_name = None
    last_name = None
    email = models.EmailField(_('email address'), unique=True, null=False, blank=False)

    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()

    username = models.CharField(
        _('username'),
        blank=False,
        null=False,
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
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


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """"
    Create a token for all users
    """
    if created:
        Token.objects.create(user=instance)


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
