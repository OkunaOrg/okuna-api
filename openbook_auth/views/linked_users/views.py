from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_auth.views.linked_users.serializers import GetLinkedUsersSerializer, \
    SearchLinkedUsersSerializer, LinkedUsersUserSerializer


class LinkedUsers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetLinkedUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')
        with_community = data.get('with_community')

        user = request.user
        users = user.get_linked_users(max_id=max_id).order_by(
            '-id')[:count]

        users_serializer = LinkedUsersUserSerializer(users, many=True, context={'request': request,
                                                                                'communities_names': [
                                                                                    with_community]})

        return Response(users_serializer.data, status=status.HTTP_200_OK)


class SearchLinkedUsers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = SearchLinkedUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')
        with_community = data.get('with_community')

        user = request.user
        users = user.search_linked_users_with_query(query=query)[:count]

        users_serializer = LinkedUsersUserSerializer(users, many=True, context={'request': request,
                                                                                'communities_names': [
                                                                                    with_community]})

        return Response(users_serializer.data, status=status.HTTP_200_OK)
