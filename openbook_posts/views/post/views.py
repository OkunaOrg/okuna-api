from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_emoji_group_model
from openbook_posts.views.post.serializers import GetPostCommentsSerializer, PostCommentSerializer, \
    CommentPostSerializer, DeletePostCommentSerializer, DeletePostSerializer, DeletePostReactionSerializer, \
    ReactToPostSerializer, PostReactionSerializer, GetPostReactionsSerializer, PostEmojiCountSerializer, \
    GetPostReactionsEmojiCountSerializer, PostReactionEmojiGroupSerializer


class PostItem(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, post_id):
        request_data = self._get_request_data(request, post_id)
        serializer = DeletePostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            user.delete_post_with_id(post_id)

        return Response({
            'message': _('Post deleted')
        }, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_id):
        request_data = request.data.copy()
        request_data['post_id'] = post_id
        return request_data


class PostComments(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_id):
        request_data = self._get_request_data(request, post_id)

        serializer = GetPostCommentsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        max_id = data.get('max_id')
        count = data.get('count', 10)
        post_id = data.get('post_id')
        user = request.user

        post_comments = user.get_comments_for_post_with_id(post_id, max_id=max_id).order_by('-created')[
                        :count]

        post_comments_serializer = PostCommentSerializer(post_comments, many=True, context={"request": request})

        return Response(post_comments_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, post_id):
        request_data = self._get_request_data(request, post_id)

        serializer = CommentPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('text')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_comment = user.comment_post_with_id(post_id=post_id, text=comment_text)

        post_comment_serializer = PostCommentSerializer(post_comment, context={"request": request})
        return Response(post_comment_serializer.data, status=status.HTTP_201_CREATED)

    def _get_request_data(self, request, post_id):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_id'] = post_id
        return request_data


class PostCommentItem(APIView):
    def delete(self, request, post_id, post_comment_id):
        request_data = self._get_request_data(request, post_id, post_comment_id)

        serializer = DeletePostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_id = data.get('post_id')
        post_comment_id = data.get('post_comment_id')
        user = request.user

        with transaction.atomic():
            user.delete_comment_with_id_for_post_with_id(post_comment_id=post_comment_id, post_id=post_id, )

        return Response({
            'message': _('Comment deleted')
        }, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_id, post_comment_id):
        request_data = request.data.copy()
        request_data['post_id'] = post_id
        request_data['post_comment_id'] = post_comment_id
        return request_data


class PostReactions(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_id):
        request_data = self._get_request_data(request, post_id)

        serializer = GetPostReactionsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_id = data.get('post_id')
        emoji_id = data.get('emoji_id')
        max_id = data.get('max_id')
        count = data.get('count', 10)
        user = request.user

        post_reactions = user.get_reactions_for_post_with_id(post_id=post_id, max_id=max_id,
                                                             emoji_id=emoji_id).order_by(
            '-created')[
                         :count]

        post_reactions_serializer = PostReactionSerializer(post_reactions, many=True, context={"request": request})

        return Response(post_reactions_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, post_id):
        request_data = self._get_request_data(request, post_id)

        serializer = ReactToPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        emoji_id = data.get('emoji_id')
        emoji_group_id = data.get('group_id')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_reaction = user.react_to_post_with_id(post_id=post_id, emoji_id=emoji_id,
                                                       emoji_group_id=emoji_group_id)

        post_reaction_serializer = PostReactionSerializer(post_reaction, context={"request": request})
        return Response(post_reaction_serializer.data, status=status.HTTP_201_CREATED)

    def _get_request_data(self, request, post_id):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_id'] = post_id
        return request_data


class PostReactionsEmojiCount(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, post_id):
        request_data = self._get_request_data(request, post_id)

        serializer = GetPostReactionsEmojiCountSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_id = data.get('post_id')
        user = request.user

        post_emoji_counts = user.get_emoji_counts_for_post_with_id(post_id)

        post_reactions_serializer = PostEmojiCountSerializer(post_emoji_counts, many=True, context={"request": request})

        return Response(post_reactions_serializer.data, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_id):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_id'] = post_id
        return request_data


class PostReactionItem(APIView):
    def delete(self, request, post_id, post_reaction_id):
        request_data = self._get_request_data(request, post_id, post_reaction_id)

        serializer = DeletePostReactionSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_id = data.get('post_id')
        post_reaction_id = data.get('post_reaction_id')
        user = request.user

        with transaction.atomic():
            user.delete_reaction_with_id_for_post_with_id(post_reaction_id=post_reaction_id, post_id=post_id, )

        return Response({
            'message': _('Reaction deleted')
        }, status=status.HTTP_200_OK)

    def _get_request_data(self, request, post_id, post_reaction_id):
        request_data = request.data.copy()
        request_data['post_id'] = post_id
        request_data['post_reaction_id'] = post_reaction_id
        return request_data


class PostReactionEmojiGroups(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        EmojiGroup = get_emoji_group_model()
        emoji_groups = EmojiGroup.objects.filter(is_reaction_group=True).all().order_by('order')
        serializer = PostReactionEmojiGroupSerializer(emoji_groups, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
