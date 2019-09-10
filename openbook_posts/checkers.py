from django.conf import settings
from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_post_model


def check_can_be_updated(post, text=None):
    if post.is_text_only_post() and not text:
        raise ValidationError(
            _('Cannot remove the text of a text only post. Try deleting it instead.')
        )


def check_is_draft(post):
    if not post.is_draft():
        raise ValidationError(
            _('Post is not a draft')
        )


def check_can_add_media(post):
    check_is_draft(post=post)
    existing_media_count = post.count_media()

    if existing_media_count >= settings.POST_MEDIA_MAX_ITEMS:
        raise ValidationError(
            _('Maximum amount of post media items reached')
        )


def check_is_not_processing(post):
    Post = get_post_model()
    if post.status == Post.STATUS_PROCESSING:
        raise ValidationError(_('The post is being processed'))


def check_is_not_published(post):
    Post = get_post_model()
    if post.status == Post.STATUS_PUBLISHED:
        raise ValidationError(_('The post is already published'))


def check_is_not_empty(post):
    if post.is_empty():
        raise ValidationError(_('The post is empty. Try adding text or media.'))


def check_can_be_published(post):
    check_is_draft(post=post)
    check_is_not_empty(post=post)


def check_mimetype_is_supported_media_mimetypes(mimetype):
    if not mimetype in settings.SUPPORTED_MEDIA_MIMETYPES:
        raise ValidationError(_('%s is not a supported mimetype') % mimetype, )
