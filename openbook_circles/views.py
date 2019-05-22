# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_circles.serializers import CreateCircleSerializer, GetCirclesCircleSerializer, DeleteCircleSerializer, \
    UpdateCircleSerializer, CircleNameCheckSerializer, GetCircleCircleSerializer
from openbook_moderation.permissions import IsNotSuspended
from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.helpers import normalise_request_data, nomalize_usernames_in_request_data


class Circles(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request):
        serializer = CreateCircleSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name = data.get('name')
        color = data.get('color')
        user = request.user

        with transaction.atomic():
            circle = user.create_circle(name=name, color=color)

        response_serializer = GetCirclesCircleSerializer(circle, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        circles = user.circles.order_by('-id')
        response_serializer = GetCirclesCircleSerializer(circles, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CircleItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, circle_id):
        user = request.user

        circle = user.get_circle_with_id(circle_id)

        response_serializer = GetCircleCircleSerializer(circle, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, circle_id):
        user = request.user
        serializer = DeleteCircleSerializer(data={'circle_id': circle_id})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user.delete_circle_with_id(circle_id)

        return Response(status=status.HTTP_200_OK)

    def patch(self, request, circle_id):
        request_data = normalise_request_data(request.data)
        request_data['circle_id'] = circle_id
        nomalize_usernames_in_request_data(request_data)

        serializer = UpdateCircleSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        circle_id = data.get('circle_id')
        color = data.get('color')
        usernames = data.get('usernames')
        name = data.get('name')

        user = request.user

        with transaction.atomic():
            circle = user.update_circle_with_id(circle_id, color=color, usernames=usernames, name=name)

        response_serializer = GetCircleCircleSerializer(circle, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CircleNameCheck(APIView):
    """
    The API to check if a circleName is both valid and not taken.
    """
    serializer_class = CircleNameCheckSerializer
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data.get('name')

        user = request.user

        if not user.has_circle_with_name(name):
            return ApiMessageResponse(_('Circle name available'), status=status.HTTP_202_ACCEPTED)

        return ApiMessageResponse(_('Circle name not available'), status=status.HTTP_400_BAD_REQUEST)
