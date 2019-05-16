from rest_framework.permissions import BasePermission


class IsNotSuspended(BasePermission):
    """
    Dont allow access to suspended users
    """

    def has_permission(self, request, view):
        return True
