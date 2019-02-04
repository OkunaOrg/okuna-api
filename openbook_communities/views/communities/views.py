# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_common.responses import ApiMessageResponse
from openbook_communities.views.communities.serializers import CreateCommunitySerializer, \
    GetCommunitiesCommunitySerializer, GetCommunitiesSerializer, CommunityNameCheckSerializer


class Communities(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = CreateCommunitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        name = data.get('name')
        type = data.get('type')
        title = data.get('title')
        description = data.get('description')
        rules = data.get('rules')
        avatar = data.get('avatar')
        cover = data.get('cover')

        user = request.user

        with transaction.atomic():
            community = user.create_community(name=name, title=title, description=description, rules=rules,
                                              avatar=avatar, cover=cover
                                              , type=type)

        response_serializer = GetCommunitiesCommunitySerializer(community, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetCommunitiesSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user

        communities = user.get_communities_with_query(query=query)[:count]

        response_serializer = GetCommunitiesCommunitySerializer(communities, many=True,
                                                                context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CommunityNameCheck(APIView):
    """
    The API to check if a communityName is both valid and not taken.
    """
    serializer_class = CommunityNameCheckSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Serializer contains validators
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return ApiMessageResponse(_('Community name available'), status=status.HTTP_202_ACCEPTED)
