from django.db import transaction
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from openbook_reports.serializers import GetReportCategoriesSerializer, ReportPostSerializer, PostReportSerializer, \
    ConfirmPostReportSerializer, PostReportConfirmSerializer
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

        serializer = ConfirmPostReportSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        report_id = data.get('report_id')
        post_id = data.get('post_id')
        user = request.user

        with transaction.atomic():
            post_report = user.confirm_report_with_id_for_post_with_id(report_id=report_id, post_id=post_id)

        post_report_serializer = PostReportConfirmSerializer(post_report, context={"request": request})
        return Response(post_report_serializer.data, status=status.HTTP_200_OK)



class ConfirmPostReports(APIView):
    permission_classes = (IsAuthenticated,)
    pass


class RejectPostReport(APIView):
    permission_classes = (IsAuthenticated,)


class RejectPostReports(APIView):
    permission_classes = (IsAuthenticated,)


class ReportedPosts(APIView):
    permission_classes = (IsAuthenticated,)


class ReportedPostsCommunity(APIView):
    permission_classes = (IsAuthenticated,)

