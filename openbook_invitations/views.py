from smtplib import SMTPException
import logging

from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalise_request_data
from openbook_invitations.serializers import GetUserInviteSerializer, CreateUserInviteSerializer, \
    GetUserInvitesSerializer, DeleteUserInviteSerializer, EmailUserInviteSerializer, EditUserInviteSerializer, \
    SearchUserInvitesSerializer
from openbook_common.responses import ApiMessageResponse

INVITE_STATUS_ALL = 'ALL'
INVITE_STATUS_PENDING = 'PENDING'
INVITE_STATUS_ACCEPTED = 'ACCEPTED'

logger = logging.getLogger(__name__)


class UserInvites(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request):
        serializer = CreateUserInviteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        nickname = data.get('nickname')
        user = request.user

        with transaction.atomic():
            invite = user.create_invite(nickname=nickname)

        response_serializer = GetUserInviteSerializer(invite, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetUserInvitesSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        offset = data.get('offset', 0)
        filter_status = data.get('pending', None)

        user = request.user
        user_invites = user.get_user_invites(status_pending=filter_status).order_by('-pk')[offset:offset + count]

        response_serializer = GetUserInviteSerializer(user_invites, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class SearchUserInvites(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = SearchUserInvitesSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')
        filter_status = data.get('pending', None)

        user = request.user
        user_invites = user.search_user_invites(status_pending=filter_status, query=query).order_by('-pk')[:count]

        response_serializer = GetUserInviteSerializer(user_invites, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UserInvite(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, invite_id):
        serializer = DeleteUserInviteSerializer(data={'invite_id': invite_id})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.delete_user_invite_with_id(invite_id)

        return ApiMessageResponse(_('Successfully deleted invite'), status=status.HTTP_200_OK)

    def patch(self, request, invite_id):
        request_data = normalise_request_data(request.data)
        request_data['invite_id'] = invite_id
        serializer = EditUserInviteSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        invite_id = serializer.validated_data.get('invite_id')
        nickname = serializer.validated_data.get('nickname')

        user = request.user

        with transaction.atomic():
            updated_invite = user.update_invite(invite_id=invite_id, nickname=nickname)

        response_serializer = GetUserInviteSerializer(updated_invite, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class SendUserInviteEmail(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, invite_id):
        request_data = normalise_request_data(request.data)
        request_data['invite_id'] = invite_id
        serializer = EmailUserInviteSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        invite_id = serializer.validated_data.get('invite_id')
        email = serializer.validated_data.get('email')

        user = request.user
        with transaction.atomic():
            try:
                user.send_invite_to_invite_id_with_email(invite_id, email)
            except SMTPException as e:
                logger.exception('Exception occurred during send_invite_email', e)
                raise APIException(_('An error occurred sending the invite, please try again'))

        return ApiMessageResponse(_('Invite email sent'), status=status.HTTP_200_OK)
