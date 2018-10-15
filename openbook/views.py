from django.utils.timezone import get_current_timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone


class Time(APIView):
    """
    The API to check if a username is both valid and not taken.
    """

    def get(self, request):
        # The serializer contains the username checks, meaning at this line, it's all good.
        time = timezone.localtime(timezone.now())
        time_zone = get_current_timezone()

        return Response({
            'time': time,
            'timezone': str(time_zone)
        }, status=status.HTTP_200_OK)
