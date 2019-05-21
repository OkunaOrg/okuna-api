from rest_framework.permissions import BasePermission


class IsNotSuspended(BasePermission):
    """
    Dont allow access to suspended users
    """

    def has_permission(self, request, view):
        if not request.user.is_anonymous:
            return not request.user.is_suspended()
        return True
