from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_user.serializers import GetUserSerializer


class GetUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user_serializer = GetUserSerializer(request.user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)
