# Create your views here.
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_circles.models import Circle
from openbook_circles.serializers import CreateCircleSerializer, CircleSerializer


class Circles(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = CreateCircleSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name = data.get('name')
        color = data.get('color')
        user = request.user

        circle = Circle.objects.create(name=name, color=color, creator=user)

        response_serializer = CircleSerializer(circle, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        response_serializer = CircleSerializer(user.circles, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CircleView(APIView):
    pass
