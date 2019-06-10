# Create your views here.
from django.db import transaction
from django.http import QueryDict
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.helpers import normalise_request_data, nomalize_usernames_in_request_data
from openbook_lists.serializers import CreateListSerializer, GetListsListSerializer, DeleteListSerializer, \
    UpdateListSerializer, \
    ListNameCheckSerializer, GetListListSerializer


class Lists(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request):
        serializer = CreateListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name = data.get('name')
        emoji_id = data.get('emoji_id')
        user = request.user

        with transaction.atomic():
            list = user.create_list(name=name, emoji_id=emoji_id)

        response_serializer = GetListsListSerializer(list, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        response_serializer = GetListsListSerializer(user.lists.order_by('-created'), many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ListItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, list_id):
        user = request.user

        list = user.get_list_with_id(list_id)

        response_serializer = GetListListSerializer(list, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, list_id):
        serializer = DeleteListSerializer(data={'list_id': list_id})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.delete_list_with_id(list_id)

        return Response(status=status.HTTP_200_OK)

    def patch(self, request, list_id):
        request_data = normalise_request_data(request.data)
        request_data['list_id'] = list_id
        nomalize_usernames_in_request_data(request_data)

        serializer = UpdateListSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        list_id = data.get('list_id')
        emoji_id = data.get('emoji_id')
        usernames = data.get('usernames')
        name = data.get('name')

        user = request.user

        with transaction.atomic():
            list = user.update_list_with_id(list_id, emoji_id=emoji_id, usernames=usernames, name=name)

        response_serializer = GetListListSerializer(list, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ListNameCheck(APIView):
    """
    The API to check if a listName is both valid and not taken.
    """
    serializer_class = ListNameCheckSerializer
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data.get('name')

        user = request.user

        if not user.has_list_with_name(name):
            return ApiMessageResponse(_('List name available'), status=status.HTTP_202_ACCEPTED)

        return ApiMessageResponse(_('List name not available'), status=status.HTTP_400_BAD_REQUEST)
