from smtplib import SMTPException

from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from openbook_common.utils.helpers import normalise_request_data
from openbook_invitations.serializers import GetUserInviteSerializer, CreateUserInviteSerializer, \
    GetUserInvitesSerializer, DeleteUserInviteSerializer, EmailUserInviteSerializer
from openbook_common.responses import ApiMessageResponse


class UserInvites(APIView):
    permission_classes = (IsAuthenticated,)

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

        user = request.user

        user_invites = user.get_user_invites()[offset:offset + count]

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
            except Exception as e:
                print('Exception occurred during send_invite_email', e)
                raise SMTPException(_('An error occurred sending the invite, please try again later'))

        return ApiMessageResponse(_('Invite email sent'), status=status.HTTP_200_OK)
