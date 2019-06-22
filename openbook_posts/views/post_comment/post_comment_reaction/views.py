from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_comment.post_comment_reaction.serializers import DeletePostCommentReactionSerializer


class PostCommentReactionItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def delete(self, request, post_uuid, post_comment_id, post_comment_reaction_id):
        request_data = {
            'post_uuid': post_uuid,
            'post_comment_reaction_id': post_comment_reaction_id,
            'post_comment_id': post_comment_id,
        }

        serializer = DeletePostCommentReactionSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.delete_post_comment_reaction_with_id(post_comment_reaction_id=post_comment_reaction_id)

        return Response({
            'message': _('Post comment reaction deleted')
        }, status=status.HTTP_200_OK)
