# Create your views here.
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_follows.serializers import FollowUserRequestSerializer, FollowSerializer, \
    DeleteFollowSerializer, UpdateFollowSerializer, FollowUserSerializer


class Follows(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        response_serializer = FollowSerializer(user.follows, many=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class FollowUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = FollowUserRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        list_id = data.get('list_id')
        user_to_follow_username = data.get('username')

        user = request.user

        User = get_user_model()
        user_to_follow = User.objects.get(username=user_to_follow_username)

        with transaction.atomic():
            follow = user.follow_user_with_id(user_to_follow.pk, list_id=list_id)

        response_serializer = FollowSerializer(follow, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UnfollowUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        serializer = DeleteFollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_to_unfollow_username = data.get('username')

        User = get_user_model()
        user_to_unfollow = User.objects.get(username=user_to_unfollow_username)

        with transaction.atomic():
            user.unfollow_user_with_id(user_to_unfollow.pk)

        response_serializer = FollowUserSerializer(user_to_unfollow, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UpdateFollowUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        serializer = UpdateFollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        list_id = data.get('list_id')
        followed_user_username = data.get('username')

        User = get_user_model()
        followed_user = User.objects.get(username=followed_user_username)

        with transaction.atomic():
            follow = user.update_follow_for_user_with_id(followed_user.pk, list_id=list_id)

        response_serializer = FollowSerializer(follow, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
