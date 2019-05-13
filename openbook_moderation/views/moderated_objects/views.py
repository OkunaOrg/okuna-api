# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.views.moderated_objects.serializers import GetModeratedObjectsSerializer, \
    ModeratedObjectSerializer


class StaffModeratedObjects(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetModeratedObjectsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')
        type = data.get('type')
        verified = data.get('verified')
        approved = data.get('approved')

        user = request.user

        moderated_objects = user.get_moderated_objects_for_staff(max_id=max_id, type=type, verified=verified,
                                                                 approved=approved).order_by('-created')[:count]

        response_serializer = ModeratedObjectSerializer(moderated_objects, many=True,
                                                        context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CommunityModeratedObjects(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name
        serializer = GetModeratedObjectsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        community_name = data.get('community_name')
        count = data.get('count', 10)
        max_id = data.get('max_id')
        type = data.get('type')
        verified = data.get('verified')
        approved = data.get('approved')

        user = request.user

        moderated_objects = user.get_moderated_objects_for_community_with_name(community_name=community_name,
                                                                               max_id=max_id, type=type,
                                                                               verified=verified,
                                                                               approved=approved).order_by('-created')[
                            :count]

        response_serializer = ModeratedObjectSerializer(moderated_objects, many=True,
                                                        context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
