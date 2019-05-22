from datetime import datetime
from json import JSONDecodeError

from rest_framework import status

from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.models import Post
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.images import ImageFile
from django.utils.dateparse import parse_datetime
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import ugettext_lazy as _

from openbook_importer.serializers import ZipfileSerializer
from openbook_importer.socialmedia_archive_parser.fb_parser import zip_parser


class ImportItem(APIView):

    permission_classes = (IsAuthenticated, IsNotSuspended)

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
            return self._return_malicious()

        if p.profile.posts:
            self.save_posts(p.profile.posts, request.user)

        return Response({
            'message': _('done')
        }, status=status.HTTP_200_OK)

    def save_posts(self, posts, user):

        for post in posts:
            image = None
            images = None
            text = None
            timestamp = post['timestamp']
            created = datetime.fromtimestamp(timestamp)
            created = parse_datetime(created.strftime('%Y-%m-%d %T+00:00'))

            if 'attachments' in post.keys():
                images = self._get_media_content(post)

            if 'data' in post.keys() and len(post['data']) != 0:
                text = post['data'][0]['post']

            if images:
                image = images[0]

                if 'text' in image.keys():
                    text = image['text']

                image = ImageFile(image['file'])

            if not Post.objects.filter(creator=user.pk, text=text, created=created).exists():
                user.create_public_post(text=text, image=image, created=created)

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
            'message':_('invalid archive')
        }, status=status.HTTP_400_BAD_REQUEST)

    def _return_malicious(self):
        # TODO LOG MALICIOUS ATTEMPT
        print('---- POTENTIALLY MALICIOUS UPLOAD!!!')

        return Response({
            'message':_('invalid archive')
        }, status=status.HTTP_400_BAD_REQUEST)
