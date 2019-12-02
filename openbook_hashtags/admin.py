from django.contrib import admin

# Register your models here.
from openbook_hashtags.models import Hashtag


class HashtagAdmin(admin.ModelAdmin):
    model = Hashtag
    search_fields = ('name',)
    exclude = ['posts', 'post_comments']


admin.site.register(Hashtag, HashtagAdmin)
