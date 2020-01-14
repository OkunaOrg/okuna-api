# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_hashtags.views.hashtag.serializers import GetHashtagHashtagSerializer
from openbook_hashtags.views.hashtags.serializers import SearchHashtagsSerializer
from openbook_moderation.permissions import IsNotSuspended


class SearchHashtags(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = SearchHashtagsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 20)
        query = data.get('query')

        user = request.user

        hashtags = user.search_hashtags_with_query(query=query)

        hashtags_serializer = GetHashtagHashtagSerializer(hashtags[:count], many=True, context={'request': request})

        return Response(hashtags_serializer.data, status=status.HTTP_200_OK)
