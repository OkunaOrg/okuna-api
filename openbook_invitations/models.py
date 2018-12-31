from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.db import models
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from openbook_auth.models import User

# Create your models here.
from openbook.settings import USERNAME_MAX_LENGTH


class InviteUser(models.Model):
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
    reward_tier_id = models.IntegerField(blank=True, null=True)
    token = models.CharField(max_length=256)
    token_was_used = models.BooleanField(default=False)

    def send_invite_email(self):
        pass

    def generate_user_token_with_expiry(self):
        pass

    def check_token_is_valid(self):
        """
        Check provided token and username combination must match
        """
        pass

    def request_new_invite_link(self):
        """
        If a user forgets to use the invite for a long time, maybe we can
        let them request a new email
        """
        self.reset_token()
        self.send_invite_email()
        pass

    def reset_token(self):
        pass

    def set_token_was_used(self):
        """
        (optional field) Once a token is used to create account, we should set a flag
        to know how many people created accounts
        """
        pass

    def is_token_expired(self):
        pass

    def generate_invitation_link(self):
        pass

    def get_user_profile_badge(self):
        """
        Checks reward tier id and returns appropriate UserProfileBadge model
        during create account
        :return: UserProfileBadge
        """
        pass
