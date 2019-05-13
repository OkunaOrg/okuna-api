from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.serializers import ModeratedObjectSerializer
from openbook_moderation.views.moderated_object.serializers import EditModeratedObjectSerializer, \
    SubmitModeratedObjectSerializer


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
        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.update_moderated_object_with_id(moderated_object_id=moderated_object_id,
                                                                    description=description, category=category,
                                                                    approved=approved, verified=verified)

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)


class SubmitModeratedObject(APIView):
    def post(self, request, moderated_object_id):
        request_data = request.data.dict()

        request_data['moderated_object_id'] = moderated_object_id
        serializer = SubmitModeratedObjectSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        moderated_object_id = data.get('moderated_object_id')

        user = request.user

        with transaction.atomic():
            moderated_object = user.submit_moderated_object_with_id(moderated_object_id=moderated_object_id)

        moderated_object_serializer = ModeratedObjectSerializer(moderated_object,
                                                                context={"request": request})

        return Response(moderated_object_serializer.data, status=status.HTTP_200_OK)
