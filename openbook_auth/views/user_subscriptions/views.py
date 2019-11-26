from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_auth.views.user_subscriptions.serializers import GetUserSubscriptionsSerializer, UserSubscriptionsUserSerializer, \
    SearchUserSubscriptionsSerializer


class UserSubscriptions(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetUserSubscriptionsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user
        users = user.get_user_subscriptions(max_id=max_id).order_by(
            '-id')[:count]

        users_serializer = UserSubscriptionsUserSerializer(users, many=True, context={'request': request})

        return Response(users_serializer.data, status=status.HTTP_200_OK)


class SearchUserSubscriptions(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = SearchUserSubscriptionsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user
        users = user.search_user_notifications_subscriptions_with_query(query=query)[:count]

        users_serializer = UserSubscriptionsUserSerializer(users, many=True, context={'request': request, })

        return Response(users_serializer.data, status=status.HTTP_200_OK)
