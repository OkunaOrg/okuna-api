from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils import six
from django.utils.translation import ugettext_lazy as _
import jwt
from openbook.settings import USERNAME_MAX_LENGTH, PROFILE_NAME_MAX_LENGTH
from openbook_common.models import Badge
from openbook_common.utils.model_loaders import get_user_invite_model
from rest_framework.exceptions import ValidationError


class UserInvite(models.Model):
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invited_users',
                                   null=True, blank=True)
    created = models.DateTimeField(_('invited datetime'), null=False, blank=False)
    created_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=PROFILE_NAME_MAX_LENGTH, null=True, blank=True)
    nickname = models.CharField(max_length=PROFILE_NAME_MAX_LENGTH, null=True, blank=True)
    email = models.EmailField(_('email address'), null=True, blank=True)
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
    badge = models.ForeignKey(Badge, blank=True, null=True, on_delete=models.SET_NULL)
    token = models.CharField(max_length=255, unique=True)
    is_invite_email_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = (('invited_by', 'email'), ('invited_by', 'nickname'),)

    def __str__(self):
        return 'UserInvite'


    @classmethod
    def is_token_valid(cls, token):
        try:
            jwt.decode(token, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        except jwt.InvalidTokenError:
            return False
        return True

    @classmethod
    def create_invite(cls, email=None, name=None, username=None, badge=None, nickname=None, invited_by=None):
        UserInvite = get_user_invite_model()
        invite = UserInvite.objects.create(nickname=nickname, name=name, email=email, username=username, badge=badge,
                                           invited_by=invited_by)
        invite.token = invite.generate_token()
        invite.save()
        return invite

    @classmethod
    def get_invite_for_token(cls, token):
        cls._check_token_is_valid(token=token)
        user_invite = UserInvite.objects.get(token=token, created_user=None)
        return user_invite

    @classmethod
    def check_token_is_valid(cls, token):
        cls._check_token_is_valid(token=token)

    @classmethod
    def _check_token_is_valid(cls, token):
        if not UserInvite.is_token_valid(token=token):
            raise ValidationError(
                _('The token is invalid.')
            )

        if not UserInvite.objects.filter(token=token).exists():
            raise ValidationError(
                _('No invite exists for given token.')
            )

        if UserInvite.objects.filter(token=token, created_user__isnull=False).exists():
            raise ValidationError(
                _('This invite has already been used.')
            )

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(UserInvite, self).save(*args, **kwargs)

    def send_invite_email(self):
        if self.invited_by:
            mail_subject = _('You\'ve been invited to join Okuna (formerly Openbook)')
            text_message_content = render_to_string('openbook_invitations/email/user_invite.txt', {
                'name': self.name,
                'invited_by_name': self.invited_by.profile.name,
                'invite_link': self._generate_one_time_link()
            })
            html_message_content = render_to_string('openbook_invitations/email/user_invite.html', {
                'name': self.name,
                'invited_by_name': self.invited_by.profile.name,
                'invite_link': self._generate_one_time_link()
            })
        else:
            mail_subject = _('You\'ve been invited to join Okuna (formerly Openbook)')
            text_message_content = render_to_string('openbook_invitations/email/backer_onboard.txt', {
                'name': self.name,
                'invite_link': self._generate_one_time_link()
            })
            html_message_content = render_to_string('openbook_invitations/email/backer_onboard.html', {
                'name': self.name,
                'invite_link': self._generate_one_time_link()
            })
        email = EmailMultiAlternatives(mail_subject, text_message_content, to=[self.email],
                                       from_email=settings.SERVICE_EMAIL_ADDRESS)
        email.attach_alternative(html_message_content, 'text/html')
        email.send()
        self.is_invite_email_sent = True
        self.save()

    def send_alternate_username_survey_email(self):
        # Hack: Since username is unique, we populate name field with username during
        # parsing of this csv so we can import all records.
        # This is a one time operation before launch.
        mail_subject = _('Action Required: Choose an alternate username for Okuna')
        text_message_content = render_to_string('openbook_invitations/email/backer_alternate_username.txt', {
            'username': self.name,
            'invite_link': 'https://openbook.typeform.com/to/MSbtq9'
        })
        html_message_content = render_to_string('openbook_invitations/email/backer_alternate_username.html', {
            'username': self.name,
            'typeform_link': 'https://openbook.typeform.com/to/MSbtq9'
        })
        email = EmailMultiAlternatives(mail_subject, text_message_content, to=[self.email],
                                       from_email=settings.SERVICE_EMAIL_ADDRESS)
        email.attach_alternative(html_message_content, 'text/html')
        email.send()
        self.is_invite_email_sent = True
        self.save()

    def generate_token(self):
        token_bytes = jwt.encode({'id': self.id}, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token_bytes.decode('UTF-8')

    def _generate_one_time_link(self):
        return '{0}/api/auth/invite?token={1}'.format(settings.EMAIL_HOST, self.token)

