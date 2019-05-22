from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_post_model
from openbook_posts.views.post.serializers import DeletePostSerializer, GetPostSerializer, GetPostPostSerializer, \
    UnmutePostSerializer, MutePostSerializer, EditPostSerializer, AuthenticatedUserEditPostSerializer, OpenClosePostSerializer, \
    OpenPostSerializer, ClosePostSerializer


# TODO Use post uuid also internally, not only as API resource identifier
# In order to prevent enumerable posts API in alpha, this is done as a hotfix

def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class PostItem(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)

        serializer = GetPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        post = user.get_post_with_id(post_id)

        post_comments_serializer = GetPostPostSerializer(post, context={"request": request})

        return Response(post_comments_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, post_uuid):
        request_data = request.data.dict()

        request_data['post_uuid'] = post_uuid
        serializer = EditPostSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        text = data.get('text', None)
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post = user.update_post(post_id=post_id, text=text)

        post_serializer = AuthenticatedUserEditPostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)
        serializer = DeletePostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            user.delete_post_with_id(post_id)

        return Response({
            'message': _('Post deleted')
        }, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        return request_data


class MutePost(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid):
        serializer = MutePostSerializer(data={
            'post_uuid': post_uuid
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            muted_post = user.mute_post_with_id(post_id=post_id)

        post_comments_serializer = GetPostPostSerializer(muted_post, context={"request": request})

        return Response(post_comments_serializer.data, status=status.HTTP_200_OK)


class UnmutePost(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid):
        serializer = UnmutePostSerializer(data={
            'post_uuid': post_uuid
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            muted_post = user.unmute_post_with_id(post_id=post_id)

        post_comments_serializer = GetPostPostSerializer(muted_post, context={"request": request})

        return Response(post_comments_serializer.data, status=status.HTTP_200_OK)


class PostClose(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid

        serializer = ClosePostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post = user.close_post_with_id(post_id=post_id)

        post_serializer = OpenClosePostSerializer(post, context={'request': request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)


class PostOpen(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid

        serializer = OpenPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post = user.open_post_with_id(post_id=post_id)

        post_serializer = OpenClosePostSerializer(post, context={'request': request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)

