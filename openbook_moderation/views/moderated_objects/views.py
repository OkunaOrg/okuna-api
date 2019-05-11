# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_common.utils.helpers import normalise_request_data


class ModeratedObjects(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetModeratedObjectsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')
        type = data.get('type')

        user = request.user

        moderatedObjects = user.get_reported_objects(max_id=max_id).order_by('-created')[:count]

        response_serializer = GetModeratedObjectsModeratedObjectserializer(moderatedObjects, many=True,
                                                                         context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)