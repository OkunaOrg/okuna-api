from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_common.peekalink_client import peekalink_client
from openbook_common.responses import ApiMessageResponse
from openbook_common.serializers import CommonSearchCommunitiesSerializer, CommonSearchCommunitiesCommunitySerializer, \
    CommonCommunityNameSerializer
from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalize_list_value_in_request_data, normalise_request_data
from openbook_posts.permissions import IsGetOrIsAuthenticated
from openbook_posts.views.posts.serializers import AuthenticatedUserPostSerializer, \
    GetPostsSerializer, UnauthenticatedUserPostSerializer, CreatePostSerializer, GetTopPostsSerializer, \
    AuthenticatedUserTopPostSerializer, GetTrendingPostsSerializer, AuthenticatedUserTrendingPostSerializer, \
    GetProfilePostsCommunityExclusionSerializer, GetTopPostsCommunityExclusionSerializer, PreviewLinkSerializer


class Posts(APIView):
    permission_classes = (IsGetOrIsAuthenticated, IsNotSuspended)

    def put(self, request):

        request_data = request.data.dict()

        normalize_list_value_in_request_data('circle_id', request_data)

        serializer = CreatePostSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        text = data.get('text')
        image = data.get('image')
        video = data.get('video')
        circles_ids = data.get('circle_id')
        is_draft = data.get('is_draft')
        user = request.user

        with transaction.atomic():
            if circles_ids:
                post = user.create_encircled_post(text=text, circles_ids=circles_ids, image=image, video=video,
                                                  is_draft=is_draft)
            else:
                post = user.create_public_post(text=text, image=image, video=video, is_draft=is_draft)

        post_serializer = AuthenticatedUserPostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        if request.user.is_authenticated:
            return self.get_posts_for_authenticated_user(request)
        return self.get_posts_for_unauthenticated_user(request)

    def get_posts_for_authenticated_user(self, request):
        query_params = request.query_params.dict()
        normalize_list_value_in_request_data('circle_id', query_params)
        normalize_list_value_in_request_data('list_id', query_params)

        serializer = GetPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        circles_ids = data.get('circle_id')
        lists_ids = data.get('list_id')
        max_id = data.get('max_id')
        min_id = data.get('min_id')
        count = data.get('count', 10)
        username = data.get('username')

        user = request.user

        if username:
            if username == user.username:
                posts = user.get_posts(max_id=max_id)
            else:
                posts = user.get_posts_for_user_with_username(username, max_id=max_id, min_id=min_id)
        else:
            posts = user.get_timeline_posts(
                circles_ids=circles_ids,
                lists_ids=lists_ids,
                max_id=max_id,
                min_id=min_id,
                count=count
            )

        posts = posts.order_by('-id')[:count]

        post_serializer_data = AuthenticatedUserPostSerializer(posts, many=True, context={"request": request}).data

        return Response(post_serializer_data, status=status.HTTP_200_OK)

    def get_posts_for_unauthenticated_user(self, request):
        query_params = request.query_params.dict()

        serializer = GetPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        max_id = data.get('max_id')
        count = data.get('count', 10)
        username = data.get('username')

        User = get_user_model()

        posts = User.get_unauthenticated_public_posts_for_user_with_username(
            max_id=max_id,
            username=username
        ).order_by('-created')[:count]

        post_serializer = UnauthenticatedUserPostSerializer(posts, many=True, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)


class TrendingPosts(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        user = request.user

        posts = user.get_trending_posts_old()[:30]
        posts_serializer = AuthenticatedUserPostSerializer(posts, many=True, context={"request": request})
        return Response(posts_serializer.data, status=status.HTTP_200_OK)


class TrendingPostsNew(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        query_params = request.query_params.dict()

        serializer = GetTrendingPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        max_id = data.get('max_id')
        min_id = data.get('min_id')
        count = data.get('count', 30)
        user = request.user

        trending_posts = user.get_trending_posts(max_id=max_id, min_id=min_id).order_by('-id')[:count]
        posts_serializer = AuthenticatedUserTrendingPostSerializer(trending_posts, many=True,
                                                                   context={"request": request})
        return Response(posts_serializer.data, status=status.HTTP_200_OK)


class TopPosts(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        query_params = request.query_params.dict()

        serializer = GetTopPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        max_id = data.get('max_id')
        min_id = data.get('min_id')
        count = data.get('count', 20)
        exclude_joined_communities = data.get('exclude_joined_communities', False)

        user = request.user

        top_posts = user.get_top_posts(max_id=max_id, min_id=min_id,
                                       exclude_joined_communities=exclude_joined_communities).order_by('-id')[:count]
        posts_serializer = AuthenticatedUserTopPostSerializer(top_posts, many=True, context={"request": request})
        return Response(posts_serializer.data, status=status.HTTP_200_OK)


class TopPostsExcludedCommunities(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetTopPostsCommunityExclusionSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        offset = data.get('offset', 0)

        user = request.user
        exclusions = user.get_top_posts_community_exclusions()[offset:offset + count]

        communities = [exclusion.community for exclusion in exclusions]

        communities_serializer = CommonSearchCommunitiesCommunitySerializer(communities, many=True,
                                                                            context={'request': request})

        return Response(communities_serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = CommonCommunityNameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        community_name = data.get('community_name')

        user = request.user

        with transaction.atomic():
            user.exclude_community_with_name_from_top_posts(community_name)

        return ApiMessageResponse(_('Community excluded from this feed'), status=status.HTTP_202_ACCEPTED)


class SearchTopPostsExcludedCommunities(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = CommonSearchCommunitiesSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 20)
        query = data.get('query')

        user = request.user

        exclusions = user.search_top_posts_excluded_communities_with_query(query=query)[:count]

        communities = [exclusion.community for exclusion in exclusions]

        response_serializer = CommonSearchCommunitiesCommunitySerializer(communities, many=True,
                                                                         context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class TopPostsExcludedCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = CommonCommunityNameSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.remove_exclusion_for_community_with_name_from_top_posts(community_name)

        return ApiMessageResponse(_('Community exclusion removed'), status=status.HTTP_202_ACCEPTED)


class ProfilePostsExcludedCommunities(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetProfilePostsCommunityExclusionSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        offset = data.get('offset', 0)

        user = request.user
        exclusions = user.get_profile_posts_community_exclusions()[offset:offset + count]

        communities = [exclusion.community for exclusion in exclusions]

        communities_serializer = CommonSearchCommunitiesCommunitySerializer(communities, many=True,
                                                                            context={'request': request})

        return Response(communities_serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = CommonCommunityNameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        community_name = data.get('community_name')

        user = request.user

        with transaction.atomic():
            user.exclude_community_with_name_from_profile_posts(community_name)

        return ApiMessageResponse(_('Community excluded from this feed'), status=status.HTTP_202_ACCEPTED)


class ProfilePostsExcludedCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = CommonCommunityNameSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.remove_exclusion_for_community_with_name_from_profile_posts(community_name)

        return ApiMessageResponse(_('Community exclusion removed'), status=status.HTTP_202_ACCEPTED)


class SearchProfilePostsExcludedCommunities(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = CommonSearchCommunitiesSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 20)
        query = data.get('query')

        user = request.user

        exclusions = user.search_profile_posts_excluded_communities_with_query(query=query)[:count]

        communities = [exclusion.community for exclusion in exclusions]

        communities_serializer = CommonSearchCommunitiesCommunitySerializer(communities, many=True,
                                                                            context={"request": request})

        return Response(communities_serializer.data, status=status.HTTP_200_OK)


class PreviewLink(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)
    throttle_scope = 'link_preview'

    def post(self, request):
        serializer = PreviewLinkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        link = data.get('link')
        user = request.user

        link_preview = user.preview_link(link=link)

        return Response(link_preview, status=status.HTTP_200_OK)


class LinkIsPreviewable(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)
    throttle_scope = 'link_preview'

    def post(self, request):
        serializer = PreviewLinkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        link = data.get('link')

        try:
            is_previewable = peekalink_client.is_peekable(link)
        except Exception as e:
            # We dont care whether it succeeded or not
            is_previewable = False

        return Response({
            'is_previewable': is_previewable
        }, status=status.HTTP_200_OK)
