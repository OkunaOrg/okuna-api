# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_circles.serializers import CreateCircleSerializer, CircleSerializer, DeleteCircleSerializer, \
    UpdateCircleSerializer


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
