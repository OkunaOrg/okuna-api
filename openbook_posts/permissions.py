from rest_framework import permissions


class IsGetOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        # allow all GET requests
        if request.method == 'GET':
            return True

        # Otherwise, only allow authenticated requests
        # Post Django 1.10, 'is_authenticated' is a read-only attribute
        return request.user and request.user.is_authenticated
