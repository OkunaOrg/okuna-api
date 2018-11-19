from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_posts.models import Post, PostComment, PostReaction


def post_id_exists(post_id):
    if Post.objects.filter(id=post_id).count() == 0:
        raise ValidationError(
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
