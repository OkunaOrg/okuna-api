from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _
from itertools import chain
import operator

from openbook_common.utils.model_loaders import get_post_model
from openbook_posts.views.post_comment.serializers import DeletePostCommentSerializer, UpdatePostCommentSerializer, \
    EditPostCommentSerializer, GetPostCommentRepliesSerializer, PostCommentReplySerializer, CommentRepliesPostSerializer

# TODO Use post uuid also internally, not only as API resource identifier
# In order to prevent enumerable posts API in alpha, this is done as a hotfix


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class PostCommentItem(APIView):
    permission_classes = (IsAuthenticated,)

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


class PostCommentReplies(APIView):
    permission_classes = (IsAuthenticated,)

    SORT_CHOICE_TO_QUERY = {
        'DESC': '-created',
        'ASC': 'created'
    }

    def get(self, request, post_uuid, post_comment_id):
        request_data = self._get_request_data(request, post_uuid, post_comment_id)

        serializer = GetPostCommentRepliesSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        max_id = data.get('max_id')
        min_id = data.get('min_id')
        count_max = data.get('count_max', 10)
        count_min = data.get('count_min', 10)
        sort = data.get('sort', 'DESC')
        post_uuid = data.get('post_uuid')
        post_comment_id = data.get('post_comment_id')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        sort_query = self.SORT_CHOICE_TO_QUERY[sort]

        if not max_id and not min_id:
            all_comment_replies = \
                user.get_comment_replies_for_post_with_id_for_comment_with_id(post_id,
                                                                              post_comment_id).order_by(
                    sort_query)[:count_max].all()
        else:
            post_comment_replies_max = []
            post_comment_replies_min = []
            if max_id:
                post_comment_replies_max = \
                    user.get_comment_replies_for_post_with_id_for_comment_with_id(post_id,
                                                                                  post_comment_id,
                                                                                  max_id=max_id).order_by('-pk')[:count_max]
                post_comment_replies_max = sorted(post_comment_replies_max.all(),
                                                  key=operator.attrgetter('created'),
                                                  reverse=sort_query == self.SORT_CHOICE_TO_QUERY['DESC'])

            if min_id:
                post_comment_replies_min = \
                    user.get_comment_replies_for_post_with_id_for_comment_with_id(post_id,
                                                                                  post_comment_id,
                                                                                  min_id=min_id).order_by('pk')[:count_min]
                post_comment_replies_min = sorted(post_comment_replies_min.all(),
                                                  key=operator.attrgetter('created'),
                                                  reverse=sort_query == self.SORT_CHOICE_TO_QUERY['DESC'])

            if sort_query == self.SORT_CHOICE_TO_QUERY['ASC']:
                all_comment_replies = list(chain(post_comment_replies_max, post_comment_replies_min))
            elif sort_query == self.SORT_CHOICE_TO_QUERY['DESC']:
                all_comment_replies = list(chain(post_comment_replies_min, post_comment_replies_max))

        post_comment_replies_serializer = PostCommentReplySerializer(all_comment_replies,
                                                                     many=True, context={"request": request})

        return Response(post_comment_replies_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, post_uuid, post_comment_id):
        request_data = self._get_request_data(request, post_uuid, post_comment_id)

        serializer = CommentRepliesPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('text')
        post_uuid = data.get('post_uuid')
        post_comment_id = data.get('post_comment_id')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_comment_reply = user.reply_to_comment_with_id_for_post_with_id(post_id=post_id,
                                                                                post_comment_id=post_comment_id,
                                                                                text=comment_text)

        post_comment_serializer = PostCommentReplySerializer(post_comment_reply, context={"request": request})
        return Response(post_comment_serializer.data, status=status.HTTP_201_CREATED)

    def _get_request_data(self, request, post_uuid, post_comment_id):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_uuid'] = post_uuid
        request_data['post_comment_id'] = post_comment_id
        return request_data
