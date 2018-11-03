from django.utils.timezone import get_current_timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone


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
    API
    """
    def get(self, request):
        return Response({
            'message': 'Todo muy bueno!'
        })
