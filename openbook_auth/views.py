from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError, APIException
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from rest_framework.authtoken.models import Token

from openbook_auth.exceptions import EmailVerificationTokenInvalid
from openbook_common.responses import ApiMessageResponse
from .serializers import RegisterSerializer, UsernameCheckSerializer, EmailCheckSerializer, LoginSerializer, \
    GetAuthenticatedUserSerializer, GetUserUserSerializer, UpdateAuthenticatedUserSerializer, GetUserSerializer, \
    GetUsersSerializer, GetUsersUserSerializer, UpdateUserSettingsSerializer, EmailVerifySerializer
from .models import UserProfile


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
        username = data.get('username')
        password = data.get('password')
        birth_date = data.get('birth_date')
        name = data.get('name')
        avatar = data.get('avatar')
        User = get_user_model()

        with transaction.atomic():
            new_user = User.objects.create_user(email=email, username=username, password=password)
            UserProfile.objects.create(name=name, user=new_user, birth_date=birth_date, avatar=avatar)

        user_auth_token = new_user.auth_token

        return Response({
            'token': user_auth_token.key
        }, status=status.HTTP_201_CREATED)


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

    def get(self, request, token):
        user = request.user
        request.data['token'] = token
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data.get('token')

        try:
            user.verify_email_with_token(token)
        except EmailVerificationTokenInvalid:
            return Response(_('Verify email token invalid or expired'), status=status.HTTP_401_UNAUTHORIZED)

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


class AuthenticatedUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user_serializer = GetAuthenticatedUserSerializer(request.user, context={"request": request})
        return Response(user_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UpdateAuthenticatedUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        with transaction.atomic():
            user.update(
                username=data.get('username'),
                name=data.get('name'),
                location=data.get('location'),
                birth_date=data.get('birth_date'),
                bio=data.get('bio'),
                url=data.get('url'),
                followers_count_visible=data.get('followers_count_visible'),
                save=False
            )

            has_avatar = 'avatar' in data
            if has_avatar:
                avatar = data.get('avatar')
                if avatar is None:
                    user.delete_profile_avatar(save=False)
                else:
                    user.update_profile_avatar(avatar, save=False)

            has_cover = 'cover' in data
            if has_cover:
                cover = data.get('cover')
                if cover is None:
                    user.delete_profile_cover(save=False)
                else:
                    user.update_profile_cover(cover, save=False)

            user.profile.save()
            user.save()

        user_serializer = GetAuthenticatedUserSerializer(user, context={"request": request})
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class UserSettings(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request):
        serializer = UpdateUserSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        with transaction.atomic():
            has_password = 'new_password' in data
            if has_password:
                current_password = data.get('current_password')
                new_password = data.get('new_password')
                if user.check_password(current_password):
                    user.update_password(password=new_password)
                else:
                    return Response(_('Password is not valid'), status=status.HTTP_400_BAD_REQUEST)
            has_email = 'email' in data
            if has_email:
                new_email = data.get('email')
                user.update_email(new_email)
                self.send_confirmation_email(request, user)

            if not has_email and not has_password:
                return Response(_('Please specify email or password to update'), status=status.HTTP_400_BAD_REQUEST)

        user_serializer = GetAuthenticatedUserSerializer(user, context={"request": request})
        return Response(user_serializer.data, status=status.HTTP_200_OK)

    def send_confirmation_email(self, request, user):
        mail_subject = _('Confirm your email for Openbook')
        current_site = get_current_site(request)
        message = render_to_string('change_email.txt', {
            'name': user.profile.name,
            'protocol': request.scheme,
            'domain': current_site.domain,
            'token': user.make_email_verification_token()
        })

        # @todo: Update from email to reflect a generic one from Openbook
        email = EmailMessage(
            mail_subject, message, to=['shantanu@open-book.org'], from_email='shantanu@open-book.org'
        )
        email.send()


class Users(APIView):
    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user

        if user.is_anonymous:
            User = get_user_model()
            users = User.get_public_users_with_query(query=query)
        else:
            users = user.get_users_with_query(query=query)

        users_serializer = GetUsersUserSerializer(users[:count], many=True, context={'request': request})

        return Response(users_serializer.data, status=status.HTTP_200_OK)


class User(APIView):
    def get(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        User = get_user_model()

        user = User.get_user_with_username(username)

        user_serializer = None

        if not request.user.is_anonymous:
            authenticated_user = request.user
            if authenticated_user.username == user_username:
                user_serializer = GetAuthenticatedUserSerializer(user, context={"request": request})

        if not user_serializer:
            user_serializer = GetUserUserSerializer(user, context={"request": request})

        return Response(user_serializer.data, status=status.HTTP_200_OK)
