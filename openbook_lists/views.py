# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_lists.models import List
from openbook_lists.serializers import CreateListSerializer, ListSerializer, DeleteListSerializer


class Lists(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = CreateListSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name = data.get('name')
        emoji_id = data.get('emoji_id')
        user = request.user

        list = List.objects.create(name=name, creator=user, emoji_id=emoji_id)

        response_serializer = ListSerializer(list, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        response_serializer = ListSerializer(user.lists, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ListItem(APIView):
    def delete(self, request, list_id):
        user = request.user
        serializer = DeleteListSerializer(data={'list_id': list_id})
        serializer.is_valid(raise_exception=True)
        list = user.lists.get(id=list_id)
        list.delete()
        return Response(status=status.HTTP_200_OK)
