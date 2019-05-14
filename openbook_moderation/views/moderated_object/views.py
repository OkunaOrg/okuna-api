from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.serializers import ModeratedObjectSerializer
from openbook_moderation.views.moderated_object.serializers import EditModeratedObjectSerializer, \
    GetModeratedObjectLogsSerializer, ModeratedObjectLogSerializer


class ModeratedObjectItem(APIView):
    def patch(self, request, moderated_object_id):
        request_data = request.data.dict()

        request_data['moderated_object_id'] = moderated_object_id
        serializer = EditModeratedObjectSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        description = data.get('description')
        category = data.get('category')
        approved = data.get('approved')
        verified = data.get('verified')
        submitted = data.get('submitted')
        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.update_moderated_object_with_id(moderated_object_id=moderated_object_id,
                                                                    description=description, category=category,
                                                                    approved=approved, verified=verified,
                                                                    submitted=submitted)

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)


class ModeratedObjectLogs(APIView):
    def get(self, request, moderated_object_id):
        request_data = request.data.dict()

        request_data['moderated_object_id'] = moderated_object_id
        serializer = GetModeratedObjectLogsSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        count = data.get('count')
        max_id = data.get('max_id')

        user = request.user

        with transaction.atomic():
            moderated_object_logs = user.get_logs_for_moderated_object_with_id(count=count, max_id=max_id)

        moderated_object_logs_serializer = ModeratedObjectLogSerializer(moderated_object_logs,
                                                                        context={"request": request})

        return Response(moderated_object_logs_serializer.data, status=status.HTTP_200_OK)
