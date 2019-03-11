from rest_framework.exceptions import ValidationError, NotFound
from django.utils.translation import ugettext_lazy as _

from openbook_posts.models import Post, PostComment, PostReaction


def post_id_exists(post_id):
    if not Post.objects.filter(id=post_id).exists():
        raise ValidationError(
            _('The post does not exist.'),
        )


def post_uuid_exists(post_uuid):
    if not Post.objects.filter(uuid=post_uuid).exists():
        raise NotFound(
            _('The post does not exist.'),
        )


def post_comment_id_exists(post_comment_id):
    if PostComment.objects.filter(id=post_comment_id).count() == 0:
        raise ValidationError(
            _('The post comment does not exist.'),
        )


def post_reaction_id_exists(post_reaction_id):
    if PostReaction.objects.filter(id=post_reaction_id).count() == 0:
        raise ValidationError(
            _('The post reaction does not exist.'),
        )
