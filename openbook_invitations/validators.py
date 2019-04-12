from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_invitations.models import UserInvite


def invite_id_exists(invite_id):
    if not UserInvite.objects.filter(id=invite_id).exists():
        raise ValidationError(
            _('The invite does not exist.'),
        )


def check_invite_not_used(invite_id):
    if not UserInvite.objects.filter(id=invite_id).exists():
        raise ValidationError(
            _('The invite does not exist.'),
        )
    invite = UserInvite.objects.get(id=invite_id)
    if invite.created_user is not None:
        raise ValidationError(
            _('The invite has already been used.'),
        )
