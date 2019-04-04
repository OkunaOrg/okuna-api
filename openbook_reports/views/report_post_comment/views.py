from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from openbook_common.utils.model_loaders import get_post_model
from openbook_reports.views.report_post_comment.serializers import ReportedPostsCommunitySerializer, \
    AuthenticatedUserPostCommentSerializer, ReportPostCommentSerializer, PostReportCommentSerializer, \
    ReportPostCommentsSerializer, ConfirmRejectPostCommentReportSerializer, PostCommentReportConfirmRejectSerializer


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class ReportedPostCommentsCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        request_data = request.data.copy()
        request_data['community_name'] = community_name
        serializer = ReportedPostsCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        community_name_serialized = serializer.validated_data.get('community_name')

        reported_posts = \
            user.get_reported_post_comments_for_community_with_name(community_name=community_name_serialized)
        community_reports_serializer = AuthenticatedUserPostCommentSerializer(reported_posts,
                                                                              many=True,
                                                                              context={"request": request})

        return Response(community_reports_serializer.data, status=status.HTTP_200_OK)


class ReportPostComment(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, post_uuid, post_comment_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        request_data['post_uuid'] = post_uuid
        serializer = ReportPostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('comment')
        category_id = data.get('category_id')
        post_comment_id = data.get('post_comment_id')
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_comment_report = user.report_post_comment_with_id_for_post_with_id(post_comment_id=post_comment_id,
                                                                                    post_id=post_id,
                                                                                    comment=comment_text,
                                                                                    category_id=category_id)

        post_report_comment_serializer = PostReportCommentSerializer(post_comment_report, context={"request": request})
        return Response(post_report_comment_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, post_uuid, post_comment_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        serializer = ReportPostCommentsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')
        user = request.user

        post_comment_reports = user.get_reports_for_comment_with_id(post_comment_id=post_comment_id)
        reports_serializer = PostReportCommentSerializer(post_comment_reports, many=True,
                                                         context={"request": request})

        return Response(reports_serializer.data, status=status.HTTP_200_OK)


class ConfirmPostCommentReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, post_comment_id, report_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        request_data['report_id'] = report_id
        request_data['post_uuid'] = post_uuid
        serializer = ConfirmRejectPostCommentReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')
        report_id = data.get('report_id')
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_comment_report = \
                user.confirm_report_with_id_for_comment_with_id_for_post_with_id(post_id=post_id,
                                                                                 post_comment_id=post_comment_id,
                                                                                 report_id=report_id)

        post_comment_report_serializer = PostCommentReportConfirmRejectSerializer(post_comment_report,
                                                                                  context={"request": request})
        return Response(post_comment_report_serializer.data, status=status.HTTP_200_OK)


class RejectPostCommentReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_uuid, post_comment_id, report_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        request_data['report_id'] = report_id
        request_data['post_uuid'] = post_uuid
        serializer = ConfirmRejectPostCommentReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')
        report_id = data.get('report_id')
        post_uuid = data.get('post_uuid')
        user = request.user

        post_id = get_post_id_for_post_uuid(post_uuid)

        with transaction.atomic():
            post_comment_report = \
                user.reject_report_with_id_for_comment_with_id_for_post_with_id(post_id=post_id,
                                                                                post_comment_id=post_comment_id,
                                                                                report_id=report_id)

        post_comment_report_serializer = PostCommentReportConfirmRejectSerializer(post_comment_report,
                                                                                  context={"request": request})
        return Response(post_comment_report_serializer.data, status=status.HTTP_200_OK)