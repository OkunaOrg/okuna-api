from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from openbook_common.responses import ApiMessageResponse
from openbook_moderation.views.report.serializers import ReportPostSerializer, ReportPostCommentSerializer, \
    ReportUserSerializer, ReportCommunitySerializer, ReportModeratedObjectSerializer
from openbook_posts.models import Post
from django.utils.translation import ugettext_lazy as _


class ReportPost(APIView):
    permission_classes = (IsAuthenticated,)

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
        post_id = Post.get_post_id_for_post_with_uuid(post_uuid=post_uuid)

        with transaction.atomic():
            user.report_post_with_id(post_id=post_id, category_id=category_id, description=description)

        return ApiMessageResponse(_('Post reported, thanks!'))


class ReportPostComment(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_comment_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id

        serializer = ReportPostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        post_comment_id = data.get('post_comment_id')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_post_comment_with_id(post_comment_id=post_comment_id, category_id=category_id,
                                             description=description)

        return ApiMessageResponse(_('Post comment reported, thanks!'))


class ReportUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, username):
        request_data = request.data.copy()
        request_data['username'] = username

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

        return ApiMessageResponse(_('User reported, thanks!'))


class ReportCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, community_name):
        request_data = request.data.copy()
        request_data['community_name'] = community_name

        serializer = ReportCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        community_name = data.get('community_name')
        description = data.get('description')
        category_id = data.get('category_id')

        community = request.community

        with transaction.atomic():
            community.report_community_with_name(community_name=community_name, category_id=category_id,
                                                 description=description)

        return ApiMessageResponse(_('Community reported, thanks!'))


class ReportModeratedObject(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, moderated_object_id):
        request_data = request.data.copy()
        request_data['moderated_object_id'] = moderated_object_id

        serializer = ReportModeratedObjectSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        moderated_object_id = data.get('moderated_object_id')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_moderated_object_with_id(moderated_object_id=moderated_object_id, category_id=category_id,
                                                 description=description)

        return ApiMessageResponse(_('Moderated object reported, thanks!'))
