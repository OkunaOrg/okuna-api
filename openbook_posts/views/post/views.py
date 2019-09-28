from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _
from webpreview import URLUnreachable, URLNotFound

from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.helpers import get_post_id_for_post_uuid
from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post.serializers import DeletePostSerializer, GetPostSerializer, GetPostPostSerializer, \
    UnmutePostSerializer, MutePostSerializer, EditPostSerializer, AuthenticatedUserEditPostSerializer, \
    OpenClosePostSerializer, \
    OpenPostSerializer, ClosePostSerializer, TranslatePostSerializer, \
    SearchPostParticipantsSerializer, PostParticipantSerializer, GetPostParticipantsSerializer, PublishPostSerializer, \
    GetPostStatusSerializer
from openbook_translation.strategies.base import TranslationClientError, UnsupportedLanguagePairException, \
    MaxTextLengthExceededError


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

        with transaction.atomic():
            post = user.update_post_with_uuid(post_uuid=post_uuid, text=text)

        post_serializer = AuthenticatedUserEditPostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)
        serializer = DeletePostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user

        with transaction.atomic():
            user.delete_post_with_uuid(post_uuid=post_uuid)

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
    permission_classes = (IsAuthenticated, IsNotSuspended)

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
    permission_classes = (IsAuthenticated, IsNotSuspended)

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


class TranslatePost(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid

        serializer = TranslatePostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        post_id = get_post_id_for_post_uuid(post_uuid)

        try:
            post, translated_text = user.translate_post_with_id(post_id=post_id)
        except UnsupportedLanguagePairException:
            return ApiMessageResponse(_('Translation between these languages is not supported.'),
                                      status=status.HTTP_400_BAD_REQUEST)
        except TranslationClientError:
            return ApiMessageResponse(_('Translation service returned an error'),
                                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except MaxTextLengthExceededError:
            return ApiMessageResponse(_('Max length of translation text exceeded.'),
                                      status=status.HTTP_400_BAD_REQUEST)

        return Response({'translated_text': translated_text}, status=status.HTTP_200_OK)


class GetPostParticipants(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_uuid):
        request_data = request.query_params.dict()

        request_data['post_uuid'] = post_uuid

        serializer = GetPostParticipantsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        post_uuid = data['post_uuid']
        count = data['count']

        post_participants = user.get_participants_for_post_with_uuid(post_uuid=post_uuid)[:count]

        serialized_participants = PostParticipantSerializer(post_participants, many=True, context={'request': request})

        return Response(serialized_participants.data, status=status.HTTP_200_OK)


class SearchPostParticipants(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid

        serializer = SearchPostParticipantsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        query = data['query']
        post_uuid = data['post_uuid']
        count = data['count']

        post_participants = user.search_participants_for_post_with_uuid(post_uuid=post_uuid, query=query)[:count]

        serialized_participants = PostParticipantSerializer(post_participants, many=True, context={'request': request})

        return Response(serialized_participants.data, status=status.HTTP_200_OK)


class PublishPost(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid):
        serializer = PublishPostSerializer(data={
            'post_uuid': post_uuid
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user

        with transaction.atomic():
            published_post = user.publish_post_with_uuid(post_uuid=post_uuid)

        post_comments_serializer = GetPostPostSerializer(published_post, context={"request": request})

        return Response(post_comments_serializer.data, status=status.HTTP_200_OK)


class PostStatus(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_uuid):
        serializer = GetPostStatusSerializer(data={
            'post_uuid': post_uuid
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user

        post_status = user.get_status_for_post_with_uuid(post_uuid=post_uuid)

        return Response({
            'status': post_status
        }, status=status.HTTP_200_OK)


class PostPreviewLinkData(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid

        serializer = GetPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)
        try:
            preview_link_data = user.get_preview_link_data_for_post_with_id(post_id)
        except URLNotFound:
            return ApiMessageResponse(_('The linked url associated for preview was not found.'),
                                      status=status.HTTP_400_BAD_REQUEST)
        except URLUnreachable:
            return ApiMessageResponse(_('The linked url associated for preview was not reachable.'),
                                      status=status.HTTP_400_BAD_REQUEST)

        return Response(preview_link_data, status=status.HTTP_200_OK)

