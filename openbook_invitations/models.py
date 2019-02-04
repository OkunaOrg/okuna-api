from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import six
from django.utils.translation import ugettext_lazy as _
import jwt
from openbook.settings import USERNAME_MAX_LENGTH
from openbook_common.models import Badge
from openbook_common.utils.model_loaders import get_user_invite_model


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
    token = models.CharField(max_length=255, unique=True)
    is_invite_email_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ('invited_by', 'email',)

    def __str__(self):
        return 'UserInvite: ' + self.username

    @classmethod
    def create_invite(cls, **kwargs):
        UserInvite = get_user_invite_model()
        invite = UserInvite.objects.create(**kwargs)
        token = invite.generate_jwt_token(invite.pk)
        invite.token = token
        invite.save()
        return invite

    @classmethod
    def get_invite_if_valid(cls, token):
        UserInvite = get_user_invite_model()
        data = UserInvite.verify_jwt_token(cls, encoded_token=token)
        user_invite = UserInvite.objects.get(pk=data['id'], token=token, created_user=None)

        return user_invite

    def send_invite_email(self):
        if self.invited_by:
            mail_subject = _('You\'ve been invited by {0} to join Openbook').format(self.invited_by.profile.name)
            text_message_content = render_to_string('openbook_invitations/email/user_invite.txt', {
                'name': self.name,
                'invited_by_name': self.invited_by.profile.name,
                'invite_link': self.generate_one_time_link()
            })
            html_message_content = render_to_string('openbook_invitations/email/user_invite.html', {
                'name': self.name,
                'invite_link': self.generate_one_time_link()
            })
        else:
            mail_subject = _('You\'ve been invited to join Openbook')
            text_message_content = render_to_string('openbook_invitations/email/backer_onboard.txt', {
                'name': self.name,
                'invite_link': self.generate_one_time_link()
            })
            html_message_content = render_to_string('openbook_invitations/email/backer_onboard.html', {
                'name': self.name,
                'invite_link': self.generate_one_time_link()
            })
        email = EmailMultiAlternatives(mail_subject, text_message_content, to=[self.email], from_email=settings.SERVICE_EMAIL_ADDRESS)
        email.attach_alternative(html_message_content, 'text/html')
        email.send()
        self.is_invite_email_sent = True
        self.save()

    def generate_jwt_token(self, user_id):
        token_bytes = jwt.encode({'id': user_id}, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token_bytes.decode('UTF-8')

    def verify_jwt_token(self, encoded_token):
        return jwt.decode(encoded_token, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def generate_one_time_link(self):
        return '{0}/api/auth/invite?token={1}'.format(settings.EMAIL_HOST, self.token)



