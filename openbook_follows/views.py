# Create your views here.
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_follows.serializers import FollowUserSerializer, FollowSerializer, \
    DeleteFollowSerializer, UpdateFollowSerializer


class Follows(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        response_serializer = FollowSerializer(user.follows, many=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class FollowUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = FollowUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user_to_follow_id = data.get('user_id')
        list_id = data.get('list_id')

        user = request.user

        with transaction.atomic():
            follow = user.follow_user_with_id(user_to_follow_id, list_id=list_id)

        response_serializer = FollowSerializer(follow, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UnfollowUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        serializer = DeleteFollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        followed_user_id = data.get('user_id')

        with transaction.atomic():
            user.unfollow_user_with_id(followed_user_id)

        return Response(status=status.HTTP_200_OK)


class UpdateFollowUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        serializer = UpdateFollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        followed_user_id = data.get('user_id')
        list_id = data.get('list_id')

        with transaction.atomic():
            follow = user.update_follow_for_user_with_id(followed_user_id, list_id=list_id)

        response_serializer = FollowSerializer(follow, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
