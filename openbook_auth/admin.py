from django.contrib import admin

# RegisterView your models here.
from openbook_auth.models import User, UserProfile


class UserProfileInline(admin.TabularInline):
    model = UserProfile

    def has_delete_permission(self, request, obj=None):
        return False


class UserAdmin(admin.ModelAdmin):
    inlines = [
        UserProfileInline,
    ]
    search_fields = ('username',)

    exclude = ('password',)

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(User, UserAdmin)
