#!/usr/bin/env python3

from json import loads
from yaml import safe_load
from hashlib import sha3_256
from zipfile import PyZipFile
from os import access, R_OK, path
from tempfile import TemporaryDirectory

from magic import from_buffer


class profile_import(object):

    friends = False
    albums = False
    messages = False
    posts = False

    def __init__(self, friends, albums, messages, posts):

        self.friends = friends
        self.albums = albums
        self.messages = messages
        self.posts = posts


class zip_parser():

    profile = False

    def __init__(self, filename):

        zipf = PyZipFile(filename)
        # test this with corrupt zipfile
        zipf.testzip()
        size = self._get_extracted_zipsize(zipf)

        # if size > 1gb
        if size > 1000000000:
            raise BufferError('filesize exceeds 1GB')

        friends = self._extract_friends(zipf)
        albums = self._extract_albums(zipf)
        messages = self._extract_messages(zipf)
        posts = self._extract_posts(zipf)

        self.profile = profile_import(friends, albums, messages, posts)

    def _file_access(self, filename):

        if not access(filename, R_OK):
            raise FileNotFoundError(f"{filename} not found")

        return True

    def _return_mime_magic(self, extension):

        mpath = 'openbook_importer/socialmedia_archive_parser'

        if not self._file_access(f"{mpath}/mimetypes.yml"):
            return False

        types = safe_load(open(f"{mpath}/mimetypes.yml", 'r'))

        if 'mimetypes' not in types:
            raise LookupError('file format incorrect, mimetypes key not found')

        types = types['mimetypes']

        if extension not in types:
            raise KeyError(f'extension not found, unknown filetype for '
                           f'{extension}')

        return types[extension]

    def _check_file_magic(self, zipf, name):

        if name.find('.') != -1:
            extension = name.split('.')[-1]
            mime = self._return_mime_magic(extension)

        else:
            raise TypeError(f"{name} filenames without extension not "
                            "allowed")

        if from_buffer(zipf.read(name), mime=True) not in mime:
            raise TypeError(f"{name}'s extension does not "
                            f"match mime-type {mime}")

    def _read_file_from_zip(self, zipf, name):

        if name in zipf.namelist():
            self._check_file_magic(zipf, name)
            return zipf.read(name)

        else:
            raise FileNotFoundError(f"{name} not found in zip file")

    def _get_extracted_zipsize(self, zipf):

        size = 0

        for entry in zipf.filelist:
            size += entry.file_size

        return size

    def _get_files_from_directory(self, dir_name, zipf, directory=False,
                                  filename=False):

        files = set()
        for entry in zipf.filelist:

            if not filename:
                if not directory and not entry.is_dir():
                    name = entry.filename

                elif directory and entry.is_dir():
                    name = entry.filename

                else:
                    name = entry.filename

                if name[0:len(dir_name)+1] == f"{dir_name}/":
                    if name != f"{dir_name}/":
                        files.add(name)

            else:
                if filename in entry.filename and not entry.is_dir():
                    name = entry.filename
                    files.add(name)

        return files

    def _write_file_to_dir(self, dir_name, item, zipf):

        i_path = path.join(dir_name, item.split('/')[-1])

        with open(i_path, 'wb+') as fd:
            fd.write(zipf.read(item))

    def _get_fd_from_file(self, dir_name, itype, item, zipf, mode='r'):

        self._write_file_to_dir(dir_name, item, zipf)

        name = item.split('/')[-1]
        fd = open(path.join(dir_name, name), mode)

        return((name, fd))

    def _parse_album_json(self, album_json, zipf):

        photo_attrs = ['uri', 'creation_timestamp', 'comments', 'description']

        json = loads(self._read_file_from_zip(zipf, album_json))

        album_name = json['name']
        album = {}
        album[album_name] = {'photos': []}
        photos = {}

        for photo in json['photos']:
            for attr in photo_attrs:
                if attr in photo.keys():
                    photos[attr] = photo[attr]

            album[album_name]['photos'].append(photos)
            photos = {}

        return album

    def _extract_albums(self, zipf):

        album_defs = self._get_files_from_directory('photos_and_videos/album',
                                                    zipf)
        albums = []

        for album in album_defs:
            albums.append(self._parse_album_json(album, zipf))

        temp = TemporaryDirectory(dir='media')

        for album in albums:
            for value in album.values():
                for file in (value['photos']):
                    file['uri'] = self._get_fd_from_file(temp.name,
                                                         'photos_and_videos',
                                                         file['uri'], zipf,
                                                         mode='rb')

        return albums

    def _extract_friends(self, zipf):

        json = loads(self._read_file_from_zip(zipf, 'friends/friends.json'))
        friends = json['friends']

        profile_info = 'profile_information/profile_information.json'
        profile_info = loads(self._read_file_from_zip(zipf, profile_info)
                             )['profile']
        full_name = profile_info['name']['full_name']

        sort_string = []
        friends_hash = []

        for friend in friends:
            sort_string.append(friend['name'])
            sort_string.append(full_name)
            sort_string.sort()

            friend_string = (f"{':'.join(sort_string)}:{friend['timestamp']}"
                             .encode('utf-8'))

            friends_hash.append(sha3_256(friend_string).hexdigest())
            sort_string = []

        return(friends_hash)

    def _parse_message(self, zipf, message):

        json = loads(self._read_file_from_zip(zipf, message))

        temp = TemporaryDirectory(dir='media')

        if 'messages' in json.keys():
            for m in json['messages']:

                if 'photos' in m.keys():
                    for p in m['photos']:
                        p['uri'] = self._get_fd_from_file(temp.name,
                                                          'messages',
                                                          p['uri'], zipf)
        else:
            raise KeyError('key messages not found in json')

        return json

    def _extract_messages(self, zipf):

        message_json = self._get_files_from_directory('messages', zipf,
                                                      filename='message.json')
        messages = []
        for message in message_json:
            messages.append(self._parse_message(zipf, message))

        return messages

    def _has_attachment(self, zipf, post):

        temp = TemporaryDirectory(dir='media')

        if 'attachments' in post.keys():
            for attachment in post['attachments']:
                if 'data' in attachment.keys():
                    for item in attachment['data']:
                        if 'media' in item.keys():
                            media = item['media']
                            uri = self._get_fd_from_file(temp.name,
                                                         media['uri'].
                                                         split('/')[0],
                                                         media['uri'], zipf,
                                                         mode='rb')
                            media['uri'] = uri

                            if 'media_metadata' in media:
                                media.pop('media_metadata')

                            return post

                        else:
                            return False

    def _extract_posts(self, zipf):

        json = loads(self._read_file_from_zip(zipf, 'posts/your_posts.json'))

        posts = []

        if 'status_updates' in json.keys():
            for post in json['status_updates']:
                media = self._has_attachment(zipf, post)

                if media:
                    post = media

                posts.append(post)

        else:
            raise KeyError('key status_updates not found in json')

        return posts
