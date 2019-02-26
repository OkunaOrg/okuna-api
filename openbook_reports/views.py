from django.db import transaction
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from openbook_reports.serializers import GetReportCategoriesSerializer, ReportPostSerializer, PostReportSerializer, \
    ConfirmRejectPostReportSerializer, PostReportConfirmRejectSerializer, AuthenticatedUserPostSerializer, \
    ReportedPostsCommunitySerializer, ReportPostCommentSerializer, PostReportCommentSerializer, \
    ReportPostCommentsSerializer, PostCommentReportConfirmRejectSerializer, \
    ConfirmRejectPostCommentReportSerializer, AuthenticatedUserPostCommentSerializer
from openbook_reports.models import ReportCategory as ReportCategoryModel


class ReportCategory(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        report_categories = ReportCategoryModel.objects.all()
        response_serializer = GetReportCategoriesSerializer(report_categories, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ReportPost(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, post_id):
        request_data = request.data.copy()
        request_data['post_id'] = post_id
        serializer = ReportPostSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('comment')
        category = data.get('category_name')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_report = user.report_post_with_id(post_id=post_id, comment=comment_text, category_name=category)

        post_report_serializer = PostReportSerializer(post_report, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_201_CREATED)


class ConfirmPostReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id, report_id):
        request_data = request.data.copy()
        request_data['post_id'] = post_id
        request_data['report_id'] = report_id

        serializer = ConfirmRejectPostReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        report_id = data.get('report_id')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_report = user.confirm_report_with_id_for_post_with_id(report_id=report_id, post_id=post_id)

        post_report_serializer = PostReportConfirmRejectSerializer(post_report, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_200_OK)


class RejectPostReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id, report_id):
        request_data = request.data.copy()
        request_data['post_id'] = post_id
        request_data['report_id'] = report_id

        serializer = ConfirmRejectPostReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        report_id = data.get('report_id')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_report = user.reject_report_with_id_for_post_with_id(report_id=report_id, post_id=post_id)

        post_report_serializer = PostReportConfirmRejectSerializer(post_report, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_200_OK)


class ReportedPosts(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        all_reported_posts_serialiazer = AuthenticatedUserPostSerializer(user.get_reported_posts(), many=True, context={"request": request})

        return Response(all_reported_posts_serialiazer.data, status=status.HTTP_200_OK)


class UserReports(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        all_reports_serialiazed = PostReportSerializer(user.get_reports(), many=True, context={"request": request})

        return Response(all_reports_serialiazed.data, status=status.HTTP_200_OK)


class ReportedPostsCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        request_data = request.data.copy()
        request_data['community_name'] = community_name
        serializer = ReportedPostsCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        community_name_serialized = serializer.validated_data.get('community_name')

        with transaction.atomic():
            reported_posts = user.get_reported_posts_for_community_with_name(community_name=community_name_serialized)
            community_reports_serializer = AuthenticatedUserPostSerializer(reported_posts,
                                                                           many=True,
                                                                           context={"request": request})

        return Response(community_reports_serializer.data, status=status.HTTP_200_OK)


class ReportedPostCommentsCommunity(APIView):
        permission_classes = (IsAuthenticated,)

        def get(self, request, community_name):
            request_data = request.data.copy()
            request_data['community_name'] = community_name
            serializer = ReportedPostsCommunitySerializer(data=request_data)
            serializer.is_valid(raise_exception=True)

            user = request.user
            community_name_serialized = serializer.validated_data.get('community_name')

            with transaction.atomic():
                reported_posts = \
                    user.get_reported_post_comments_for_community_with_name(community_name=community_name_serialized)
                community_reports_serializer = AuthenticatedUserPostCommentSerializer(reported_posts,
                                                                                      many=True,
                                                                                      context={"request": request})

            return Response(community_reports_serializer.data, status=status.HTTP_200_OK)


class ReportPostComment(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, post_id, post_comment_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        request_data['post_id'] = post_id
        serializer = ReportPostCommentSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        comment_text = data.get('comment')
        category = data.get('category_name')
        post_comment_id = data.get('post_comment_id')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_comment_report = user.report_post_comment_with_id_for_post_with_id(post_comment_id=post_comment_id,
                                                                                    post_id=post_id,
                                                                                    comment=comment_text,
                                                                                    category_name=category)

        post_report_comment_serializer = PostReportCommentSerializer(post_comment_report, context={"request": request})
        return Response(post_report_comment_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, post_id, post_comment_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        serializer = ReportPostCommentsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')
        user = request.user

        with transaction.atomic():
            post_comment_reports = user.get_reports_for_comment_with_id(post_comment_id=post_comment_id)
            reports_serializer = PostReportCommentSerializer(post_comment_reports, many=True,
                                                             context={"request": request})

        return Response(reports_serializer.data, status=status.HTTP_200_OK)


class ConfirmPostCommentReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id, post_comment_id, report_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        request_data['report_id'] = report_id
        request_data['post_id'] = post_id
        serializer = ConfirmRejectPostCommentReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')
        report_id = data.get('report_id')
        post_id = data.get('post_id')
        user = request.user

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

    def post(self, request, post_id, post_comment_id, report_id):
        request_data = request.data.copy()
        request_data['post_comment_id'] = post_comment_id
        request_data['report_id'] = report_id
        request_data['post_id'] = post_id
        serializer = ConfirmRejectPostCommentReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_comment_id = data.get('post_comment_id')
        report_id = data.get('report_id')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_comment_report = \
                user.reject_report_with_id_for_comment_with_id_for_post_with_id(post_id=post_id,
                                                                                post_comment_id=post_comment_id,
                                                                                report_id=report_id)

        post_comment_report_serializer = PostCommentReportConfirmRejectSerializer(post_comment_report,
                                                                                  context={"request": request})
        return Response(post_comment_report_serializer.data, status=status.HTTP_200_OK)

