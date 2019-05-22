# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalize_list_value_in_request_data
from openbook_moderation.serializers import ModeratedObjectSerializer
from openbook_moderation.views.moderated_objects.serializers import \
    GetCommunityModeratedObjectsSerializer, GetGlobalModeratedObjectsSerializer


class GlobalModeratedObjects(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        query_params = request.query_params.dict()
        normalize_list_value_in_request_data(request_data=query_params, list_name='types')
        normalize_list_value_in_request_data(request_data=query_params, list_name='statuses')

        serializer = GetGlobalModeratedObjectsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')
        types = data.get('types')
        verified = data.get('verified')
        statuses = data.get('statuses')

        user = request.user

        moderated_objects = user.get_global_moderated_objects(max_id=max_id, types=types,
                                                              verified=verified,
                                                              statuses=statuses).order_by('-id')[
                            :count]

        response_serializer = ModeratedObjectSerializer(moderated_objects, many=True,
                                                        context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CommunityModeratedObjects(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        normalize_list_value_in_request_data(request_data=query_params, list_name='types')
        normalize_list_value_in_request_data(request_data=query_params, list_name='statuses')

        query_params['community_name'] = community_name
        serializer = GetCommunityModeratedObjectsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        community_name = data.get('community_name')
        count = data.get('count', 10)
        max_id = data.get('max_id')
        types = data.get('types')
        verified = data.get('verified')
        statuses = data.get('statuses')

        user = request.user

        moderated_objects = user.get_community_moderated_objects(community_name=community_name,
                                                                 max_id=max_id,
                                                                 verified=verified,
                                                                 types=types,
                                                                 statuses=statuses).order_by('-id')[
                            :count]

        response_serializer = ModeratedObjectSerializer(moderated_objects, many=True,
                                                        context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
