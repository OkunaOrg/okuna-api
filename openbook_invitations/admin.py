from django.contrib import admin
from openbook_invitations.models import UserInvite



class UserInviteAdmin(admin.ModelAdmin):
    model = UserInvite
    search_fields = ('username', 'email')
    list_display = ('name', 'username', 'email', 'created_user', 'badge')
    list_display_links = ['email', 'username']

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(UserInvite, UserInviteAdmin)
