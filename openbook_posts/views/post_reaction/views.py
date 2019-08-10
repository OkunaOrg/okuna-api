from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _


# TODO Use post uuid also internally, not only as API resource identifier
# In order to prevent enumerable posts API in alpha, this is done as a hotfix
from openbook_common.utils.model_loaders import get_post_model
from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_reaction.serializers import DeletePostReactionSerializer


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class PostReactionItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def delete(self, request, post_uuid, post_reaction_id):
        request_data = self._get_request_data(request, post_uuid, post_reaction_id)

        serializer = DeletePostReactionSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        post_reaction_id = data.get('post_reaction_id')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            user.delete_reaction_with_id_for_post_with_id(post_reaction_id=post_reaction_id, post_id=post_id, )

        return Response({
            'message': _('Reaction deleted')
        }, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_uuid, post_reaction_id):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        request_data['post_reaction_id'] = post_reaction_id
        return request_data
