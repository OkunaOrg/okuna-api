from django.utils.timezone import get_current_timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from openbook_common.serializers import EmojiGroupSerializer, EmojiSerializer
from openbook_common.utils.model_loaders import get_emoji_group_model, get_emoji_model


class Time(APIView):
    """
    API for returning the current time.
    """

    def get(self, request):
        time = timezone.localtime(timezone.now())
        time_zone = get_current_timezone()

        return Response({
            'time': time,
            'timezone': str(time_zone)
        }, status=status.HTTP_200_OK)


class Health(APIView):
    """
    API for checking the app health
    """

    def get(self, request):
        return Response({
            'message': 'Todo muy bueno!'
        })


class EmojiGroups(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        EmojiGroup = get_emoji_group_model()
        emoji_groups = EmojiGroup.objects.filter(is_reaction_group=False).all().order_by('order')
        serializer = EmojiGroupSerializer(emoji_groups, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
