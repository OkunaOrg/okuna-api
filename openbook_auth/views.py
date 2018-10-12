from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

from openbook.responses import ApiMessageResponse
from .serializers import RegisterSerializer, UsernameCheckSerializer, EmailCheckSerializer
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

        return ApiMessageResponse('User successfully created', status=status.HTTP_201_CREATED)


class UsernameCheck(APIView):
    """
    The API to check if a username is both valid and not taken.
    """
    serializer_class = UsernameCheckSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # The serializer contains the username checks, meaning at this line, it's all good.
        return ApiMessageResponse('Username available', status=status.HTTP_202_ACCEPTED)


class EmailCheck(APIView):
    """
    The API to check if a email is both valid and not taken.
    """
    serializer_class = EmailCheckSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # The serializer contains the email checks, meaning at this line, it's all good.
        return ApiMessageResponse('Email available', status=status.HTTP_202_ACCEPTED)
