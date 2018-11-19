from django.contrib import admin

# Register your models here.
from openbook_common.models import Emoji


class EmojiAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'created',
        'keyword',
        'color',
    )


admin.site.register(Emoji, EmojiAdmin)
