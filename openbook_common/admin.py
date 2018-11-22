from django.contrib import admin

# Register your models here.
from openbook_common.models import Emoji, EmojiGroup


class EmojiGroupEmoji(admin.TabularInline):
    model = Emoji


class EmojiGroupAdmin(admin.ModelAdmin):
    inlines = [
        EmojiGroupEmoji
    ]

    list_display = (
        'id',
        'keyword',
        'created',
        'color',
        'order'
    )

    readonly_fields = (
        'keyword',
    )


admin.site.register(EmojiGroup, EmojiGroupAdmin)
