from django.contrib import admin
from django.contrib.admin import ModelAdmin
from modeltranslation.admin import TranslationAdmin

from openbook_moderation.models import ModerationCategory, ModerationReport, ModeratedObject


class ModerationCategoryAdmin(TranslationAdmin):
    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(ModerationCategory, ModerationCategoryAdmin)


class ModerationReportAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    readonly_fields = ['reporter', 'moderated_object', 'category', 'description']


admin.site.register(ModerationReport, ModerationReportAdmin)


class ModeratedObjectAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    readonly_fields = ['verified', 'category', 'description', 'community', 'status', 'object_type', 'object_id', 'content_type']


admin.site.register(ModeratedObject, ModeratedObjectAdmin)
