from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_common.utils.helpers import normalise_request_data
from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_comment.post_comment_reaction.serializers import PostCommentReactionSerializer
from openbook_posts.views.post_comment.post_comment_reactions.serializers import GetPostCommentReactionsSerializer, \
    ReactToPostCommentSerializer, GetPostCommentReactionsEmojiCountSerializer, PostCommentEmojiCountSerializer


class PostCommentReactions(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, post_uuid, post_comment_id):
        request_data = request.query_params.dict()
        request_data['post_uuid'] = post_uuid
        request_data['post_comment_id'] = post_comment_id

        serializer = GetPostCommentReactionsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')
        emoji_id = data.get('emoji_id')
        max_id = data.get('max_id')
        count = data.get('count', 10)

        user = request.user

        post_comment_reactions = user.get_reactions_for_post_comment_with_id(post_comment_id=post_comment_id,
                                                                             max_id=max_id,
                                                                             emoji_id=emoji_id).order_by('-id')[:count]

        post_reactions_serializer = PostCommentReactionSerializer(post_comment_reactions, many=True,
                                                                  context={"request": request})

        return Response(post_reactions_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, post_uuid, post_comment_id):
        request_data = normalise_request_data(request.data)
        request_data.update(request.query_params.dict())
        request_data['post_uuid'] = post_uuid
        request_data['post_comment_id'] = post_comment_id

        serializer = ReactToPostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        emoji_id = data.get('emoji_id')

        user = request.user

        with transaction.atomic():
            post_comment_reaction = user.react_to_post_comment_with_id(post_comment_id=post_comment_id,
                                                                       emoji_id=emoji_id, )

        post_reaction_serializer = PostCommentReactionSerializer(post_comment_reaction, context={"request": request})
        return Response(post_reaction_serializer.data, status=status.HTTP_201_CREATED)


class PostCommentReactionsEmojiCount(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, post_uuid, post_comment_id):
        request_data = {
            'post_uuid': post_uuid,
            'post_comment_id': post_comment_id
        }

        serializer = GetPostCommentReactionsEmojiCountSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        post_comment_emoji_counts = user.get_emoji_counts_for_post_comment_with_id(post_comment_id=post_comment_id)

        post_reactions_serializer = PostCommentEmojiCountSerializer(post_comment_emoji_counts, many=True,
                                                                    context={"request": request})

        return Response(post_reactions_serializer.data, status=status.HTTP_200_OK)
