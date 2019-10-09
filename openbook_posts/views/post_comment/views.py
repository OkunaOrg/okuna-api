from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.helpers import get_post_id_for_post_uuid
from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_comment.serializers import DeletePostCommentSerializer, UpdatePostCommentSerializer, \
    EditPostCommentSerializer, MutePostCommentSerializer, UnmutePostCommentSerializer, TranslatePostCommentSerializer, \
    GetPostCommentSerializer, GetPostCommentRequestSerializer
from openbook_translation.strategies.base import UnsupportedLanguagePairException, TranslationClientError, \
    MaxTextLengthExceededError


class PostCommentItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, post_uuid, post_comment_id):
        serializer = GetPostCommentRequestSerializer(data={
            'post_uuid': post_uuid,
            'post_comment_id': post_comment_id
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        post_comment_id = data.get('post_comment_id')

        user = request.user

        post_comment = user.get_comment_with_id_for_post_with_uuid(post_comment_id=post_comment_id,
                                                                   post_uuid=post_uuid)

        post_comment_serializer = GetPostCommentSerializer(post_comment, context={"request": request})
        return Response(post_comment_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, post_uuid, post_comment_id):
        request_data = self._get_request_data(request, post_uuid, post_comment_id)

        serializer = DeletePostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        post_comment_id = data.get('post_comment_id')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            user.delete_comment_with_id_for_post_with_id(post_comment_id=post_comment_id, post_id=post_id)

        return Response({
            'message': _('Comment deleted')
        }, status=status.HTTP_200_OK)

    def patch(self, request, post_uuid, post_comment_id):
        request_data = self._get_request_data(request, post_uuid, post_comment_id)

        serializer = UpdatePostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('text')
        post_uuid = data.get('post_uuid')
        post_comment_id = data.get('post_comment_id')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_comment = user.update_comment_with_id_for_post_with_id(post_comment_id=post_comment_id,
                                                                        post_id=post_id, text=comment_text)

        post_comment_serializer = EditPostCommentSerializer(post_comment, context={"request": request})
        return Response(post_comment_serializer.data, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_uuid, post_comment_id):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        request_data['post_comment_id'] = post_comment_id
        return request_data


class MutePostComment(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, post_comment_id):
        serializer = MutePostCommentSerializer(data={
            'post_uuid': post_uuid,
            'post_comment_id': post_comment_id,
        })
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.mute_post_comment_with_id(post_comment_id=post_comment_id)

        return ApiMessageResponse(message=_('Post comment muted.'), status=status.HTTP_200_OK)


class UnmutePostComment(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, post_comment_id):
        serializer = UnmutePostCommentSerializer(data={
            'post_uuid': post_uuid,
            'post_comment_id': post_comment_id,
        })
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.unmute_post_comment_with_id(post_comment_id=post_comment_id)

        return ApiMessageResponse(message=_('Post comment unmuted.'), status=status.HTTP_200_OK)


class TranslatePostComment(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, post_comment_id):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        request_data['post_comment_id'] = post_comment_id

        serializer = TranslatePostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')

        try:
            post_comment, translated_text = user.translate_post_comment_with_id(post_comment_id=post_comment_id)
        except UnsupportedLanguagePairException:
            return ApiMessageResponse(_('Translation between these languages is not supported.'),
                                      status=status.HTTP_400_BAD_REQUEST)
        except TranslationClientError:
            return ApiMessageResponse(_('Translation service returned an error'),
                                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except MaxTextLengthExceededError:
            return ApiMessageResponse(_('Max length of translation text exceeded.'),
                                      status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'translated_text': translated_text
        }, status=status.HTTP_200_OK)
