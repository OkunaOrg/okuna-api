from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.translation import ugettext_lazy as _
from rest_framework import status


class ProxyAuth(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        preview_url = request.META.get('HTTP_X_PROXY_URL')
        user = request.user

        user.check_url_allowed_for_proxy(preview_url)

        return Response(_('All Ok'), status=status.HTTP_202_ACCEPTED)







