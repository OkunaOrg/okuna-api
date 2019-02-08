import logging
from datetime import datetime
from json import JSONDecodeError

from django.db import transaction
from rest_framework import status
from openbook_posts.models import Post
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.images import ImageFile
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import ugettext_lazy as _

from openbook_importer.models import Import, ImportedPost, ImportedFriend
from openbook_importer.facebook_archive_parser.zipparser import zip_parser
from openbook_importer.serializers import ZipfileSerializer, ImportSerializer

log = logging.getLogger('security')


class ImportItem(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ZipfileSerializer(data=request.FILES)
        serializer.is_valid(raise_exception=True)

        zipfile = request.FILES['file']
        new_friends = False
        new_posts = False

        try:
            p = zip_parser(zipfile)

        except FileNotFoundError:
            raise ValidationError(
                _('Invalid archive!'),
            )

        except JSONDecodeError:
            raise ValidationError(
                _('Invalid archive!'),
            )

        except TypeError:
            log.info("Potentially malicious import prevented: "
                     f"{request.user.pk}")
            raise ValidationError(
                _('Invalid archive!'),
            )

        if p.profile.posts:
            new_posts = self._create_posts(p.profile.posts, request.user)

        if p.profile.friends:
            new_friends = self._get_friends(p.profile.friends, request.user)

        self.process_imports(new_posts, new_friends, request.user)

        return Response(status=status.HTTP_200_OK)

    def process_imports(self, new_posts, new_friends, user):

        if new_posts or new_friends:
            data_import = Import.create_import(user)

        if new_posts:
            self.save_posts(new_posts, user, data_import)

        if new_friends:
            self.save_friends(new_friends, user, data_import)

    def save_posts(self, new_posts, user, data_import):

        for new_post in new_posts:
            text, image, created = new_post

            with transaction.atomic():
                post = user.create_post(text=text, image=image,
                                        created=created)
                ImportedPost.create_imported_post(post, data_import)

    def save_friends(self, new_hashes, user, data_import):

        for friend_hash in new_hashes:
            with transaction.atomic():
                ImportedFriend.create_imported_friend(friend_hash, user)

    def _create_posts(self, posts_data, user):

        new_posts = []

        # Decrease complexity

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

    def _friend_link_exists(self, friend_hash, user):

        friend = ImportedFriend.find_friend(friend_hash, user)

        return friend

    def _get_friends(self, friend_hashes, user):

        new_friends = []

        for friend_hash in friend_hashes:
            if not self._friend_link_exists(friend_hash, user):
                new_friends.append(friend_hash)

        return new_friends

    def _get_media_content(self, post):

        # add video

        images = []
        image = {}

        # simplify
        for attachment in post['attachments']:
            for data in attachment['data']:
                image['file'] = data['media']['uri'][1]

                if 'description' in data['media'].keys():
                    image['text'] = data['media']['description']

                images.append(image)
                image = {}

        return images


class ImportedItem(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request, archive_id):

        archive = request.user.imports.filter(id=archive_id)
        if archive.exists():
            serialized = ImportSerializer(archive, many=True)

        else:
            raise ValidationError(
                _('Archive does not exist!'),
            )

        return Response(serialized.data, status=status.HTTP_200_OK)

    def delete(self, request, archive_id):

        request.user.delete_archive_with_id(archive_id)

        return Response({'Message': 'done'}, status=status.HTTP_200_OK)


class ImportedItems(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        archives = request.user.imports.all()
        serialized = ImportSerializer(archives, many=True)

        return Response(serialized.data, status=status.HTTP_200_OK)
