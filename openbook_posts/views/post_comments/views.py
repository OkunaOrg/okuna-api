from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from itertools import chain
import operator

# TODO Use post uuid also internally, not only as API resource identifier
# In order to prevent enumerable posts API in alpha, this is done as a hotfix
from openbook_common.utils.model_loaders import get_post_model
from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_comments.serializers import EnableDisableCommentsPostSerializer, \
    EnableCommentsPostSerializer, DisableCommentsPostSerializer, GetPostCommentsSerializer, PostCommentSerializer, \
    CommentPostSerializer


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class PostComments(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)
    SORT_CHOICE_TO_QUERY = {
        'DESC': '-created',
        'ASC': 'created'
    }

    def get(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)

        serializer = GetPostCommentsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        max_id = data.get('max_id')
        min_id = data.get('min_id')
        count_max = data.get('count_max', 10)
        count_min = data.get('count_min', 10)
        sort = data.get('sort', 'DESC')
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        sort_query = self.SORT_CHOICE_TO_QUERY[sort]

        if not max_id and not min_id:
            all_comments = user.get_comments_for_post_with_id(post_id).order_by(sort_query)[:count_max].all()
        else:
            post_comments_max = []
            post_comments_min = []
            if max_id:
                post_comments_max = user.get_comments_for_post_with_id(post_id,
                                                                       max_id=max_id).order_by('-pk')[:count_max]
                post_comments_max = sorted(post_comments_max.all(),
                                           key=operator.attrgetter('created'),
                                           reverse=sort_query == self.SORT_CHOICE_TO_QUERY['DESC'])

            if min_id:
                post_comments_min = user.get_comments_for_post_with_id(post_id,
                                                                       min_id=min_id).order_by('pk')[:count_min]
                post_comments_min = sorted(post_comments_min.all(),
                                           key=operator.attrgetter('created'),
                                           reverse=sort_query == self.SORT_CHOICE_TO_QUERY['DESC'])

            if sort_query == self.SORT_CHOICE_TO_QUERY['ASC']:
                all_comments = list(chain(post_comments_max, post_comments_min))
            elif sort_query == self.SORT_CHOICE_TO_QUERY['DESC']:
                all_comments = list(chain(post_comments_min, post_comments_max))

        post_comments_serializer = PostCommentSerializer(all_comments, many=True, context={"request": request,
                                                                                           "sort_query": sort_query})

        return Response(post_comments_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)

        serializer = CommentPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('text')
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_comment = user.comment_post_with_id(post_id=post_id, text=comment_text)

        post_comment_serializer = PostCommentSerializer(post_comment, context={"request": request})
        return Response(post_comment_serializer.data, status=status.HTTP_201_CREATED)

    def _get_request_data(self, request, post_uuid):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_uuid'] = post_uuid
        return request_data


class PostCommentsDisable(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        serializer = DisableCommentsPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user
        post_uuid = data.get('post_uuid')
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post = user.disable_comments_for_post_with_id(post_id=post_id)

        post_serializer = EnableDisableCommentsPostSerializer(post, context={"request": request})
        return Response(post_serializer.data, status=status.HTTP_200_OK)


class PostCommentsEnable(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        serializer = EnableCommentsPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user
        post_uuid = data.get('post_uuid')
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post = user.enable_comments_for_post_with_id(post_id=post_id)

        post_serializer = EnableDisableCommentsPostSerializer(post, context={"request": request})
        return Response(post_serializer.data, status=status.HTTP_200_OK)
