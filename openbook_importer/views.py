from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
from django.utils.translation import ugettext_lazy as _
from rest_framework.parsers import FileUploadParser

from .models import Posts
from openbook_importer.serializers import ZipfileSerializer
from openbook_importer.facebook_archive_parser.zipparser import zip_parser


class ImportItem(APIView):

    def post(self, request):
        serializer = ZipfileSerializer(data=request.FILES)
        serializer.is_valid(raise_exception=True)

        zipfile = request.FILES['file']

        p = zip_parser(zipfile)
        self.save_posts(p.profile.posts)

        return Response({
            'message': _('done')
        }, status=status.HTTP_200_OK)

    def save_posts(self, posts):

        for post in posts:
            posts_db = Posts()
            posts_db.timestamp = post['timestamp']

            if len(post['data']) == 1:
                posts_db.post = post['data'][0]['post']

            else:
                raise ValueError('data is not the expected length')
            posts_db.title = post['title']

            posts_db.save()
