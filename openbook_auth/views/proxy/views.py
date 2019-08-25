from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.translation import ugettext_lazy as _
from rest_framework import status

from openbook_auth.views.proxy.serializers import ProxyAuthSerializer
from openbook_common import checkers as common_checkers


class ProxyAuth(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        url = request.META.get('HTTP_X_PROXY_URL', '')

        serializer = ProxyAuthSerializer(data={
            'url': url
        })

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        url = data.get('url')

        common_checkers.check_url_can_be_proxied(url)

        return Response(_('All Ok'), status=status.HTTP_202_ACCEPTED)
