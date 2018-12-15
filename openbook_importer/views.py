from datetime import datetime

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import ugettext_lazy as _

from openbook_importer.serializers import ZipfileSerializer
from openbook_importer.facebook_archive_parser.zipparser import zip_parser


class ImportItem(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ZipfileSerializer(data=request.FILES)
        serializer.is_valid(raise_exception=True)

        zipfile = request.FILES['file']

        p = zip_parser(zipfile)
        self.save_posts(p.profile.posts, request.user)

        return Response({
            'message': _('done')
        }, status=status.HTTP_200_OK)

    def save_posts(self, posts, user):

        for post in posts:
            timestamp = post['timestamp']
            created = datetime.fromtimestamp(timestamp)
            created = parse_datetime(created.strftime('%Y-%m-%d %T'))

            if len(post['data']) == 1:
                text = post['data'][0]['post']

            else:
                raise ValueError('data is not the expected length')

            user.create_post(text, created=created)
