from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from openbook_common.responses import ApiMessageResponse
from openbook_posts.models import Post
from django.utils.translation import ugettext_lazy as _


class ReportPost(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, post_uuid):
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

    def put(self, request, post_comment_id):
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

    def put(self, request, user_id):
        request_data = request.data.copy()
        request_data['user_id'] = user_id

        serializer = ReportUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user_id = data.get('user_id')
        description = data.get('description')
        category_id = data.get('category_id')

        user = request.user

        with transaction.atomic():
            user.report_user_with_id(user_id=user_id, category_id=category_id,
                                     description=description)

        return ApiMessageResponse(_('User reported, thanks!'))


class ReportCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, community_id):
        request_data = request.data.copy()
        request_data['community_id'] = community_id

        serializer = ReportCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        community_id = data.get('community_id')
        description = data.get('description')
        category_id = data.get('category_id')

        community = request.community

        with transaction.atomic():
            community.report_community_with_id(community_id=community_id, category_id=category_id,
                                               description=description)

        return ApiMessageResponse(_('Community reported, thanks!'))


class ReportReportingAbuse(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, reported_object_id):
        request_data = request.data.copy()
        request_data['reported_object_id'] = reported_object_id

        serializer = ReportReportingAbuseSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        reported_object_id = data.get('reported_object_id')
        description = data.get('description')
        category_id = data.get('category_id')

        reportingAbuse = request.reportingAbuse

        with transaction.atomic():
            reportingAbuse.report_reporting_abuse(reported_object_id=reported_object_id, category_id=category_id,
                                                  description=description)

        return ApiMessageResponse(_('Reporting abuse reported, thanks!'))
