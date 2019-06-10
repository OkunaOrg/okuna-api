from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_moderation.views.user.serializers import GetUserModerationPenaltiesSerializer, \
    ModerationPenaltySerializer, GetUserPendingModeratedObjectsCommunities, PendingModeratedObjectsCommunitySerializer


class UserModerationPenalties(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()

        serializer = GetUserModerationPenaltiesSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        moderated_objects = user.get_moderation_penalties(max_id=max_id, ).order_by('-id')[
                            :count]

        response_serializer = ModerationPenaltySerializer(moderated_objects, many=True,
                                                          context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UserPendingModeratedObjectsCommunities(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        query_params = request.query_params.dict()

        serializer = GetUserPendingModeratedObjectsCommunities(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        communities = user.get_pending_moderated_objects_communities(max_id=max_id, ).order_by('-id')[
                      :count]

        response_serializer = PendingModeratedObjectsCommunitySerializer(communities, many=True,
                                                                         context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
