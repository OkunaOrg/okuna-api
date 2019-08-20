from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


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


def check_can_set_image(post):
    if hasattr(post, 'image') and post.image:
        raise ValidationError(
            _('Post already has an image')
        )