import logging
from datetime import datetime
from json import JSONDecodeError

from rest_framework import status
from openbook_posts.models import Post
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.images import ImageFile
from django.utils.dateparse import parse_datetime
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import ugettext_lazy as _

from openbook_importer.models import Import, ImportedPost
from openbook_importer.serializers import ZipfileSerializer
from openbook_importer.facebook_archive_parser.zipparser import zip_parser

log = logging.getLogger('security')


class ImportItem(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ZipfileSerializer(data=request.FILES)
        serializer.is_valid(raise_exception=True)

        zipfile = request.FILES['file']

        try:
            p = zip_parser(zipfile)

        except FileNotFoundError:
            return self._return_invalid()

        except JSONDecodeError:
            return self._return_invalid()

        except TypeError:
            return self._return_malicious(request.user.pk)

        if p.profile.posts:
            data_import = Import.create_import()
            new_posts = self._create_posts(p.profile.posts, request.user)

        if new_posts:
            self.save_posts(new_posts, request.user, data_import)

        return Response({
            'message': _('done')
        }, status=status.HTTP_200_OK)

    def save_posts(self, new_posts, user, data_import):

        for new_post in new_posts:
            text, image, created = new_post

            post = user.create_post(text=text, image=image,
                                    created=created)
            ImportedPost.create_imported_post(post, data_import)

    def _create_posts(self, posts_data, user):

        new_posts = []

        for post_data in posts_data:
            image = None
            images = None
            text = None
            timestamp = post_data['timestamp']
            created = datetime.fromtimestamp(timestamp)
            created = parse_datetime(created.strftime('%Y-%m-%d %T+00:00'))

            if 'attachments' in post_data.keys():
                images = self._get_media_content(post_data)

            if 'data' in post_data.keys() and len(post_data['data']) != 0:
                text = post_data['data'][0]['post']

            if images:
                # Currently we only support having one post per image
                image = images[0]

                if 'text' in image.keys():
                    text = image['text']

                image = ImageFile(image['file'])

            if not self._post_exists(user.pk, text=text,
                                     created=created):
                new_posts.append((text, image, created))

        return new_posts

    def _post_exists(self, creator, text, created):
        return Post.objects.filter(creator=creator, text=text,
                                   created=created).exists()

    def _get_media_content(self, post):

        images = []
        image = {}

        for attachment in post['attachments']:
            for data in attachment['data']:
                image['file'] = data['media']['uri'][1]

                if 'description' in data['media'].keys():
                    image['text'] = data['media']['description']

                images.append(image)
                image = {}

        return images

    def _return_invalid(self):

        return Response({
            'message': _('invalid archive')
        }, status=status.HTTP_400_BAD_REQUEST)

    def _return_malicious(self, pk):
        log.info(f"Potentially malicious import prevented {pk}")

        return Response({
            'message':  _('invalid archive')
        }, status=status.HTTP_400_BAD_REQUEST)
