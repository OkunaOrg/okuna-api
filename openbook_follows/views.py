# Create your views here.
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_auth.models import User
from openbook_circles.models import Circle
from openbook_follows.models import Follow
from openbook_follows.serializers import CreateFollowSerializer, FollowSerializer, \
    DeleteFollowSerializer


class Follows(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = CreateFollowSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user_id = data.get('user_id')
        list_id = data.get('list_id')

        user = request.user
        followed_user = User.objects.get(pk=user_id)

        follow = Follow.objects.create(user=user, followed_user=followed_user, list_id=list_id)

        response_serializer = FollowSerializer(follow, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        response_serializer = FollowSerializer(user.follows, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class FollowItem(APIView):
    def delete(self, request, follow_id):
        user = request.user
        serializer = DeleteFollowSerializer(data={'follow_id': follow_id}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        follow = user.follows.get(id=follow_id)
        follow.delete()
        return Response(status=status.HTTP_200_OK)
