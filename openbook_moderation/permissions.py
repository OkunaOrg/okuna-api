from django.contrib.humanize.templatetags.humanize import naturaltime
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from django.utils.translation import ugettext_lazy as _


class IsNotSuspended(BasePermission):
    """
    Dont allow access to suspended users
    """

    def has_permission(self, request, view):
        user = request.user
        return check_user_is_not_suspended(user=user)


def check_user_is_not_suspended(user):
    if not user.is_anonymous:
        is_suspended = user.is_suspended()
        if is_suspended:
            longest_suspension = user.get_longest_moderation_suspension()

            raise PermissionDenied(
                _('Your account has been suspended and will be unsuspended in %s' % naturaltime(
                    longest_suspension.expiration)))

    return True
