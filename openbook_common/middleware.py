import pytz

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):
    """
    A middleware to activate the user timezone if it has been stored in the session.
    """

    def process_request(self, request):
        tzname = request.META.get('HTTP_TIME_ZONE')
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
