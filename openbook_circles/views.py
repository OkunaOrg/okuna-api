# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_circles.serializers import CreateCircleSerializer, CircleSerializer, DeleteCircleSerializer, \
    UpdateCircleSerializer, CircleNameCheckSerializer
from openbook_common.responses import ApiMessageResponse


class Circles(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = CreateCircleSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name = data.get('name')
        color = data.get('color')
        user = request.user

        with transaction.atomic():
            circle = user.create_circle(name=name, color=color)

        response_serializer = CircleSerializer(circle, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        response_serializer = CircleSerializer(user.circles, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CircleItem(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, circle_id):
        user = request.user
        serializer = DeleteCircleSerializer(data={'circle_id': circle_id})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user.delete_circle_with_id(circle_id)

        return Response(status=status.HTTP_200_OK)

    def patch(self, request, circle_id):
        request_data = request.data.copy()
        request_data['circle_id'] = circle_id

        serializer = UpdateCircleSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        with transaction.atomic():
            user.update_circle_with_id(**data)

        return Response(status=status.HTTP_200_OK)


class CircleNameCheck(APIView):
    """
    The API to check if a circleName is both valid and not taken.
    """
    serializer_class = CircleNameCheckSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data.get('name')

        user = request.user

        if not user.has_circle_with_name(name):
            return ApiMessageResponse(_('Circle name available'), status=status.HTTP_202_ACCEPTED)

        return ApiMessageResponse(_('Circle name not available'), status=status.HTTP_400_BAD_REQUEST)
