from django.utils.timezone import get_current_timezone
from rest_framework import status
from rest_framework.views import APIView

from openbook.responses import ApiMessageResponse
from django.utils.translation import gettext as _
from django.utils import timezone


class Time(APIView):
    """
    The API to check if a username is both valid and not taken.
    """

    def get(self, request):
        # The serializer contains the username checks, meaning at this line, it's all good.
        return ApiMessageResponse(
            _('The time is %(time)s on timezone %(timezone)s') % {'time': timezone.localtime(timezone.now()),
                                                                  'timezone': get_current_timezone()},
            status=status.HTTP_202_ACCEPTED)
