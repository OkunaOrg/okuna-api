from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from openbook_auth.views.top_posts.serializers import TopPostExclusionCommunitySerializer, \
    GetTopPostCommunityExclusionSerializer


class TopPostCommunityExclusions(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetTopPostCommunityExclusionSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user
        exclusions = user.get_top_post_community_exclusions(max_id=max_id).order_by(
            '-id')[:count]

        communities = [exclusion.community for exclusion in exclusions]

        users_serializer = TopPostExclusionCommunitySerializer(communities, many=True, context={'request': request})

        return Response(users_serializer.data, status=status.HTTP_200_OK)
