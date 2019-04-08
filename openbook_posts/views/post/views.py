from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from itertools import chain
import operator

from openbook_common.utils.model_loaders import get_emoji_group_model, get_post_model
from openbook_posts.views.post.serializers import GetPostCommentsSerializer, PostCommentSerializer, \
    CommentPostSerializer, DeletePostCommentSerializer, DeletePostSerializer, DeletePostReactionSerializer, \
    ReactToPostSerializer, PostReactionSerializer, GetPostReactionsSerializer, PostEmojiCountSerializer, \
    GetPostReactionsEmojiCountSerializer, PostReactionEmojiGroupSerializer, GetPostSerializer, GetPostPostSerializer, \
    UnmutePostSerializer, MutePostSerializer, UpdatePostCommentSerializer, EditPostCommentSerializer, \
    EditPostSerializer, AuthenticatedUserEditPostSerializer


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


class PostComments(APIView):
    permission_classes = (IsAuthenticated,)
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

        post_comments_serializer = PostCommentSerializer(all_comments, many=True, context={"request": request})

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


class PostReactions(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)

        serializer = GetPostReactionsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        emoji_id = data.get('emoji_id')
        max_id = data.get('max_id')
        count = data.get('count', 10)

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        post_reactions = user.get_reactions_for_post_with_id(post_id=post_id, max_id=max_id,
                                                             emoji_id=emoji_id).order_by(
            '-created')[
                         :count]

        post_reactions_serializer = PostReactionSerializer(post_reactions, many=True, context={"request": request})

        return Response(post_reactions_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)

        serializer = ReactToPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        emoji_id = data.get('emoji_id')
        emoji_group_id = data.get('group_id')
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_reaction = user.react_to_post_with_id(post_id=post_id, emoji_id=emoji_id,
                                                       emoji_group_id=emoji_group_id)

        post_reaction_serializer = PostReactionSerializer(post_reaction, context={"request": request})
        return Response(post_reaction_serializer.data, status=status.HTTP_201_CREATED)

    def _get_request_data(self, request, post_uuid):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_uuid'] = post_uuid
        return request_data


class PostReactionsEmojiCount(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_uuid):
        request_data = self._get_request_data(request, post_uuid)

        serializer = GetPostReactionsEmojiCountSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        post_emoji_counts = user.get_emoji_counts_for_post_with_id(post_id)

        post_reactions_serializer = PostEmojiCountSerializer(post_emoji_counts, many=True, context={"request": request})

        return Response(post_reactions_serializer.data, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_uuid):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_uuid'] = post_uuid
        return request_data


class PostReactionItem(APIView):
    permission_classes = (IsAuthenticated,)

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


class PostReactionEmojiGroups(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        EmojiGroup = get_emoji_group_model()
        emoji_groups = EmojiGroup.objects.filter(is_reaction_group=True).all().order_by('order')
        serializer = PostReactionEmojiGroupSerializer(emoji_groups, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
