from django.contrib.contenttypes import admin

from .models import Format


class FormatInline(admin.GenericTabularInline):
    model = Format
    fields = ('format', 'progress', 'file', 'width', 'height', 'duration')
    readonly_fields = fields
    extra = 0
    max_num = 0

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False
