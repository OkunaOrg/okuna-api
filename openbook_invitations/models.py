from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.db import models
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from openbook_auth.models import User

# Create your models here.
from openbook.settings import USERNAME_MAX_LENGTH


class UserInvite(models.Model):
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invited_users')
    invited_date = models.DateField(_('invited date'), null=False, blank=False)
    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()
    username = models.CharField(
        _('username'),
        blank=True,
        null=True,
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        help_text=_('Required. %(username_max_length)d characters or fewer. Letters, digits and _ only.' % {
            'username_max_length': USERNAME_MAX_LENGTH}),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    badge_keyword = models.CharField(max_length=16, blank=True, null=True)
    token = models.CharField(max_length=256)

    def send_invite_email(self):
        pass

    def generate_user_token(self):
        pass

    def check_token_is_valid(self):
        """
        Check provided token and username combination must match
        """
        pass

    def reset_token(self):
        pass
