from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_auth.views.blocked_users.serializers import GetBlockedUsersSerializer, \
    SearchBlockedUsersSerializer, BlockedUsersUserSerializer


class BlockedUsers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetBlockedUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user
        users = user.get_blocked_users(max_id=max_id).order_by(
            '-id')[:count]

        users_serializer = BlockedUsersUserSerializer(users, many=True, context={'request': request, })

        return Response(users_serializer.data, status=status.HTTP_200_OK)


class SearchBlockedUsers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = SearchBlockedUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user
        users = user.search_blocked_users_with_query(query=query)[:count]

        users_serializer = BlockedUsersUserSerializer(users, many=True, context={'request': request, })

        return Response(users_serializer.data, status=status.HTTP_200_OK)
