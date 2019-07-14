from rest_framework.exceptions import ValidationError, NotFound
from django.utils.translation import ugettext_lazy as _

from openbook_posts.models import Post, PostComment, PostReaction, PostCommentReaction

SORT_CHOICES = ['ASC', 'DESC']


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
    if not PostComment.objects.filter(id=post_comment_id).exists():
        raise ValidationError(
            _('The post comment does not exist.'),
        )


def post_comment_id_exists_for_post_with_uuid(post_comment_id, post_uuid):
    if not PostComment.objects.filter(id=post_comment_id, post__uuid=post_uuid).exists():
        raise ValidationError(
            _('The post comment does not exist.'),
        )


def post_comment_reaction_id_exists_for_post_with_uuid_and_comment_with_id(post_comment_reaction_id, post_comment_id,
                                                                           post_uuid):
    if not PostCommentReaction.objects.filter(id=post_comment_reaction_id, post_comment_id=post_comment_id,
                                              post_comment__post__uuid=post_uuid).exists():
        raise ValidationError(
            _('The post comment reaction does not exist.'),
        )


def post_reaction_id_exists(post_reaction_id):
    if not PostReaction.objects.filter(id=post_reaction_id).exists():
        raise ValidationError(
            _('The post reaction does not exist.'),
        )


def post_comment_reaction_id_exists(post_comment_reaction_id):
    if not PostCommentReaction.objects.filter(id=post_comment_reaction_id).exists():
        raise ValidationError(
            _('The post comment reaction does not exist.'),
        )
