from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_moderation.serializers import ModeratedObjectSerializer
from openbook_moderation.views.moderated_object.serializers import UpdateModeratedObjectSerializer, \
    GetModeratedObjectLogsSerializer, ModeratedObjectLogSerializer, ApproveModeratedObjectSerializer, \
    GetModeratedObjectReportsSerializer, ModeratedObjectReportSerializer


class ModeratedObjectItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def patch(self, request, moderated_object_id):
        request_data = request.data.copy()

        request_data['moderated_object_id'] = moderated_object_id
        serializer = UpdateModeratedObjectSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        description = data.get('description')
        category_id = data.get('category_id')
        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.update_moderated_object_with_id(moderated_object_id=moderated_object_id,
                                                                    description=description, category_id=category_id, )

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)


class ApproveModeratedObject(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, moderated_object_id):
        serializer = ApproveModeratedObjectSerializer(data={
            'moderated_object_id': moderated_object_id
        }, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.approve_moderated_object_with_id(moderated_object_id=moderated_object_id, )

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)


class RejectModeratedObject(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, moderated_object_id):
        serializer = ApproveModeratedObjectSerializer(data={
            'moderated_object_id': moderated_object_id
        }, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.reject_moderated_object_with_id(moderated_object_id=moderated_object_id, )

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)


class VerifyModeratedObject(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, moderated_object_id):
        serializer = ApproveModeratedObjectSerializer(data={
            'moderated_object_id': moderated_object_id
        }, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.verify_moderated_object_with_id(moderated_object_id=moderated_object_id, )

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)


class UnverifyModeratedObject(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, moderated_object_id):
        serializer = ApproveModeratedObjectSerializer(data={
            'moderated_object_id': moderated_object_id
        }, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.unverify_moderated_object_with_id(moderated_object_id=moderated_object_id, )

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)


class ModeratedObjectLogs(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, moderated_object_id):
        request_data = request.query_params.dict()

        request_data['moderated_object_id'] = moderated_object_id
        serializer = GetModeratedObjectLogsSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        count = data.get('count')
        max_id = data.get('max_id')
        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object_logs = user.get_logs_for_moderated_object_with_id(max_id=max_id,
                                                                               moderated_object_id=moderated_object_id).order_by(
                '-id')[:count]

        moderated_object_logs_serializer = ModeratedObjectLogSerializer(moderated_object_logs, many=True,
                                                                        context={"request": request})

        return Response(moderated_object_logs_serializer.data, status=status.HTTP_200_OK)


class ModeratedObjectReports(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, moderated_object_id):
        request_data = request.query_params.dict()

        request_data['moderated_object_id'] = moderated_object_id
        serializer = GetModeratedObjectReportsSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        count = data.get('count')
        max_id = data.get('max_id')
        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object_reports = user.get_reports_for_moderated_object_with_id(max_id=max_id,
                                                                                     moderated_object_id=moderated_object_id).order_by(
                '-id')[
                                       :count]

        moderated_object_reports_serializer = ModeratedObjectReportSerializer(moderated_object_reports,
                                                                              many=True,
                                                                              context={"request": request})

        return Response(moderated_object_reports_serializer.data, status=status.HTTP_200_OK)
