from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_common.utils.model_loaders import get_emoji_group_model, get_post_model


# TODO Use post uuid also internally, not only as API resource identifier
# In order to prevent enumerable posts API in alpha, this is done as a hotfix
from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_reactions.serializers import GetPostReactionsSerializer, \
    GetPostReactionsEmojiCountSerializer, PostEmojiCountSerializer, PostReactionEmojiGroupSerializer, \
    ReactToPostSerializer
from openbook_posts.views.post_reaction.serializers import PostReactionSerializer


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class PostReactions(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

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
        post_uuid = data.get('post_uuid')

        user = request.user
        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_reaction = user.react_to_post_with_id(post_id=post_id, emoji_id=emoji_id,)

        post_reaction_serializer = PostReactionSerializer(post_reaction, context={"request": request})
        return Response(post_reaction_serializer.data, status=status.HTTP_201_CREATED)

    def _get_request_data(self, request, post_uuid):
        request_data = request.data.copy()
        query_params = request.query_params.dict()
        request_data.update(query_params)
        request_data['post_uuid'] = post_uuid
        return request_data


class PostReactionsEmojiCount(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

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


class PostReactionEmojiGroups(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        EmojiGroup = get_emoji_group_model()
        emoji_groups = EmojiGroup.objects.filter(is_reaction_group=True).all().order_by('order')
        serializer = PostReactionEmojiGroupSerializer(emoji_groups, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
