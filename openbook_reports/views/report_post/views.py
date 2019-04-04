from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from openbook_common.utils.model_loaders import get_post_model
from openbook_reports.views.report_post.serializers import ReportPostSerializer, PostReportSerializer, \
    GetPostReportSerializer, ConfirmRejectPostReportSerializer, PostReportConfirmRejectSerializer, AuthenticatedUserPostSerializer
from openbook_reports.views.report_post_comment.serializers import ReportedPostsCommunitySerializer


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class ReportPost(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        serializer = ReportPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('comment')
        category_id = data.get('category_id')
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_report = user.report_post_with_id(post_id=post_id, comment=comment_text, category_id=category_id)

        post_report_serializer = PostReportSerializer(post_report, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, post_uuid):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        serializer = GetPostReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)
        post_reports = user.get_reports_for_post_with_id(post_id=post_id)

        post_report_serializer = PostReportSerializer(post_reports, many=True, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_200_OK)


class ConfirmPostReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, report_id):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        request_data['report_id'] = report_id

        serializer = ConfirmRejectPostReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        report_id = data.get('report_id')
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_report = user.confirm_report_with_id_for_post_with_id(report_id=report_id, post_id=post_id)

        post_report_serializer = PostReportConfirmRejectSerializer(post_report, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_200_OK)


class RejectPostReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, report_id):
        request_data = request.data.copy()
        request_data['post_uuid'] = post_uuid
        request_data['report_id'] = report_id

        serializer = ConfirmRejectPostReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        report_id = data.get('report_id')
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_report = user.reject_report_with_id_for_post_with_id(report_id=report_id, post_id=post_id)

        post_report_serializer = PostReportConfirmRejectSerializer(post_report, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_200_OK)


class ReportedPosts(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        all_reported_posts_serializer = AuthenticatedUserPostSerializer(user.get_reported_posts(),
                                                                        many=True,
                                                                        context={"request": request})

        return Response(all_reported_posts_serializer.data, status=status.HTTP_200_OK)


class ReportedPostsCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        request_data = request.data.copy()
        request_data['community_name'] = community_name
        serializer = ReportedPostsCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        community_name_serialized = serializer.validated_data.get('community_name')

        reported_posts = user.get_reported_posts_for_community_with_name(community_name=community_name_serialized)
        community_reports_serializer = AuthenticatedUserPostSerializer(reported_posts,
                                                                       many=True,
                                                                       context={"request": request})

        return Response(community_reports_serializer.data, status=status.HTTP_200_OK)


class UserReports(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        all_reports_serialiazed = PostReportSerializer(user.get_post_reports(), many=True, context={"request": request})

        return Response(all_reports_serialiazed.data, status=status.HTTP_200_OK)