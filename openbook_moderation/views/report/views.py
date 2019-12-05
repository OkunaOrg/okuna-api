from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.responses import ApiMessageResponse
from openbook_moderation.views.report.serializers import ReportPostSerializer, ReportPostCommentSerializer, \
    ReportUserSerializer, ReportCommunitySerializer, ReportModeratedObjectSerializer, ReportHashtagSerializer
from django.utils.translation import ugettext_lazy as _


class ReportPost(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid

        serializer = ReportPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        post_uuid = data.get('post_uuid')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_post_with_uuid(post_uuid=post_uuid, category_id=category_id, description=description)

        return ApiMessageResponse(_('Post reported, thanks!'), status=status.HTTP_201_CREATED)


class ReportPostComment(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, post_comment_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        request_data['post_uuid'] = post_uuid

        serializer = ReportPostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        post_uuid = data.get('post_uuid')
        post_comment_id = data.get('post_comment_id')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_comment_with_id_for_post_with_uuid(post_comment_id=post_comment_id, post_uuid=post_uuid,
                                                           category_id=category_id,
                                                           description=description)

        return ApiMessageResponse(_('Post comment reported, thanks!'), status=status.HTTP_201_CREATED)


class ReportUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = ReportUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_user_with_username(username=username, category_id=category_id,
                                           description=description)

        return ApiMessageResponse(_('User reported, thanks!'), status=status.HTTP_201_CREATED)


class ReportHashtag(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, hashtag_name):
        request_data = request.data.copy()
        request_data['hashtag_name'] = hashtag_name

        serializer = ReportHashtagSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        hashtag_name = data.get('hashtag_name')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_hashtag_with_name(hashtag_name=hashtag_name, category_id=category_id,
                                          description=description)

        return ApiMessageResponse(_('Hashtag reported, thanks!'), status=status.HTTP_201_CREATED)


class ReportCommunity(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, community_name):
        request_data = request.data.copy()
        request_data['community_name'] = community_name

        serializer = ReportCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        community_name = data.get('community_name')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_community_with_name(community_name=community_name, category_id=category_id,
                                            description=description)

        return ApiMessageResponse(_('Community reported, thanks!'), status=status.HTTP_201_CREATED)
