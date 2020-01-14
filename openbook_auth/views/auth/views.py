from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from rest_framework.authtoken.models import Token

from openbook_auth.views.auth.serializers import RegisterSerializer, UsernameCheckSerializer, EmailCheckSerializer, \
    EmailVerifySerializer, LoginSerializer, VerifyPasswordResetSerializer, RequestPasswordResetSerializer, \
    RegisterTokenSerializer
from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.model_loaders import get_user_invite_model


class Register(APIView):
    """
    The API to register a new user
    """
    parser_classes = (MultiPartParser, FormParser,)
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.on_valid_request_data(serializer.validated_data)

    def on_valid_request_data(self, data):
        email = data.get('email')
        password = data.get('password')
        is_of_legal_age = data.get('is_of_legal_age')
        are_guidelines_accepted = data.get('are_guidelines_accepted')
        name = data.get('name')
        username = data.get('username')
        avatar = data.get('avatar')
        token = data.get('token')
        User = get_user_model()
        UserInvite = get_user_invite_model()

        user_invite = UserInvite.get_invite_for_token(token=token)

        if not username:
            username = user_invite.username

        if not username and not user_invite.username:
            username = User.get_temporary_username(email)

        with transaction.atomic():
            new_user = User.create_user(username=username, email=email, password=password, name=name, avatar=avatar,
                                        is_of_legal_age=is_of_legal_age, badge=user_invite.badge,
                                        are_guidelines_accepted=are_guidelines_accepted)
            user_invite.created_user = new_user
            user_invite.save()

        user_auth_token = new_user.auth_token

        return Response({
            'token': user_auth_token.key,
            'username': new_user.username
        }, status=status.HTTP_201_CREATED)


class VerifyRegistrationToken(APIView):
    """
    The API to verify a registration token
    """

    def post(self, request):
        serializer = RegisterTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        token = validated_data.get('token')

        UserInvite = get_user_invite_model()

        # raises error if invalid
        UserInvite.check_token_is_valid(token=token)

        return ApiMessageResponse(_('Token valid'), status=status.HTTP_202_ACCEPTED)


class UsernameCheck(APIView):
    """
    The API to check if a username is both valid and not taken.
    """
    serializer_class = UsernameCheckSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # The serializer contains the username checks, meaning at this line, it's all good.
        return ApiMessageResponse(_('Username available'), status=status.HTTP_202_ACCEPTED)


class EmailCheck(APIView):
    """
    The API to check if a email is both valid and not taken.
    """
    serializer_class = EmailCheckSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # The serializer contains the email checks, meaning at this line, it's all good.
        return ApiMessageResponse(_('Email available'), status=status.HTTP_202_ACCEPTED)


class EmailVerify(APIView):
    """
    The API to verify if a email is valid.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = EmailVerifySerializer

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data.get('token')

        user.verify_email_with_token(token)

        return ApiMessageResponse(_('Email verified'), status=status.HTTP_200_OK)


class Login(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.on_valid_request_data(serializer.validated_data)

    def on_valid_request_data(self, data):
        username = data['username']
        password = data['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            raise AuthenticationFailed()


class PasswordResetVerify(APIView):
    def post(self, request):
        request_data = request.data
        serializer = VerifyPasswordResetSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        token = data.get('token')
        new_password = data.get('new_password')

        User = get_user_model()
        user = User.get_user_for_password_reset_token(token)

        with transaction.atomic():
            user.verify_password_reset_token(token=token, password=new_password)

        return ApiMessageResponse(_('Password set successfully'), status=status.HTTP_200_OK)


class PasswordResetRequest(APIView):
    def post(self, request):
        request_data = request.data
        serializer = RequestPasswordResetSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        User = get_user_model()
        email = data.get('email')
        user = User.get_user_with_email(email)

        with transaction.atomic():
            user.request_password_reset()

        return ApiMessageResponse(_('A password reset link was sent to the email'), status=status.HTTP_200_OK)


class PasswordResetVerify(APIView):
    def post(self, request):
        request_data = request.data
        serializer = VerifyPasswordResetSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        token = data.get('token')
        new_password = data.get('new_password')

        User = get_user_model()
        user = User.get_user_for_password_reset_token(token)

        with transaction.atomic():
            user.verify_password_reset_token(token=token, password=new_password)

        return ApiMessageResponse(_('Password set successfully'), status=status.HTTP_200_OK)
