# Create your views here.
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.translation import gettext as _
from openbook_common.responses import ApiMessageResponse
from openbook_common.serializers import CommonFollowRequestSerializer
from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalise_request_data
from openbook_follows.serializers import FollowUserRequestSerializer, FollowSerializer, \
    DeleteFollowSerializer, UpdateFollowSerializer, FollowUserSerializer, RequestToFollowUserSerializer, \
    ApproveUserFollowRequestSerializer, RejectUserFollowRequestSerializer, ReceivedFollowRequestsRequestSerializer


class ReceivedFollowRequests(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        query_params = request.query_params.dict()
        user = request.user

        serializer = ReceivedFollowRequestsRequestSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        max_id = data.get('max_id')
        count = data.get('count', 10)

        received_follow_requests = user.get_received_follow_requests(max_id=max_id).order_by(
            '-id')[:count]

        response_serializer = CommonFollowRequestSerializer(received_follow_requests, many=True,
                                                            context={'request': request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RequestToFollowUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request):
        serializer = RequestToFollowUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_to_request_to_follow_username = data.get('username')

        user = request.user

        with transaction.atomic():
            follow_request = user.create_follow_request_for_user_with_username(user_to_request_to_follow_username)

        response_serializer = CommonFollowRequestSerializer(follow_request, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CancelRequestToFollowUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        serializer = RequestToFollowUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_to_cancel_request_for = data.get('username')

        user = request.user

        with transaction.atomic():
            user.delete_follow_request_for_user_with_username(user_to_cancel_request_for)

        return ApiMessageResponse(_('Follow request cancelled.'), status=status.HTTP_200_OK)


class ApproveUserFollowRequest(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        serializer = ApproveUserFollowRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_to_approve_follow_request_from_username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.approve_follow_request_from_user_with_username(
                user_username=user_to_approve_follow_request_from_username)

        return ApiMessageResponse(_('Follow request approved.'), status=status.HTTP_200_OK)


class RejectUserFollowRequest(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        serializer = RejectUserFollowRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_to_reject_follow_request_from_username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.reject_follow_request_from_user_with_username(
                user_username=user_to_reject_follow_request_from_username)

        return ApiMessageResponse(_('Follow request rejected.'), status=status.HTTP_200_OK)


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
