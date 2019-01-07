import uuid
from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.core.mail import EmailMessage
from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import six
from django.utils.translation import ugettext_lazy as _

# Create your models here.
from openbook.settings import USERNAME_MAX_LENGTH


class UserInvite(models.Model):
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invited_users', null=True, blank=True)
    invited_date = models.DateField(_('invited date'), null=False, blank=False, auto_now_add=True)
    created_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.EmailField(_('email address'),  null=True, blank=True)
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
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invite_email_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ('invited_by', 'email',)

    def __str__(self):
        return 'UserInvite: ' + self.username

    def send_invite_email(self):
        if self.invited_by:
            mail_subject = _('You\'ve been invited by {0} to join Openbook').format(self.invited_by.profile.name)
            message = render_to_string('user_invite.html', {
                'name': self.name,
                'invited_by_name': self.invited_by.profile.name,
                'invite_link': self.generate_one_time_link()
            })
        else:
            mail_subject = _('You\'ve been invited to join Openbook')
            message = render_to_string('backer_onboard.html', {
                'name': self.name,
                'invite_link': self.generate_one_time_link()
            })
        email = EmailMessage(mail_subject, message, to=[self.email], from_email=settings.SERVICE_EMAIL_ADDRESS)
        email.send()

    def generate_one_time_link(self):
        return '{0}/api/auth/invite?token={1}'.format(settings.EMAIL_HOST, self.token)

    def check_token_is_valid(self, token):
        return self.token == token

