from django.contrib import admin

# RegisterView your models here.
from openbook_posts.models import Post, PostImage, PostComment, PostReaction


class PostImageInline(admin.TabularInline):
    model = PostImage

    def has_delete_permission(self, request, obj=None):
        return False


class PostCommentInline(admin.TabularInline):
    model = PostComment

    readonly_fields = (
        'commenter',
        'text',
        'created'
    )

    def has_add_permission(self, request, obj):
        return False


class PostAdmin(admin.ModelAdmin):
    inlines = [
        PostImageInline,
        PostCommentInline
    ]

    list_display = (
        'id',
        'created',
        'creator',
        'comments_count',
        'reactions_count',
        'has_text',
        'has_image'
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Post, PostAdmin)
