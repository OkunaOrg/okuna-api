# Create your views here.
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalise_request_data
from openbook_follows.serializers import FollowUserRequestSerializer, FollowSerializer, \
    DeleteFollowSerializer, UpdateFollowSerializer, FollowUserSerializer


class Follows(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        response_serializer = FollowSerializer(user.follows, many=True, context={'request': request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class FollowUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        request_data = _prepare_request_data_for_validation(request.data)

        serializer = FollowUserRequestSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lists_ids = data.get('lists_ids')
        user_to_follow_username = data.get('username')

        user = request.user

        User = get_user_model()
        user_to_follow = User.objects.get(username=user_to_follow_username)

        with transaction.atomic():
            follow = user.follow_user_with_id(user_to_follow.pk, lists_ids=lists_ids)

        response_serializer = FollowSerializer(follow, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UnfollowUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

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
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        request_data = _prepare_request_data_for_validation(request.data)

        user = request.user
        serializer = UpdateFollowSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lists_ids = data.get('lists_ids')
        followed_user_username = data.get('username')

        User = get_user_model()
        followed_user = User.objects.get(username=followed_user_username)

        with transaction.atomic():
            follow = user.update_follow_for_user_with_id(followed_user.pk, lists_ids=lists_ids)

        response_serializer = FollowSerializer(follow, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


def _prepare_request_data_for_validation(request_data):
    request_data_copy = normalise_request_data(request_data)
    lists_ids = request_data_copy.get('lists_ids', None)
    if isinstance(lists_ids, str):
        lists_ids = lists_ids.split(',')
        request_data_copy['lists_ids'] = lists_ids
    return request_data_copy
