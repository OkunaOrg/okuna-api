import colorsys
import os
import random
import re
import secrets
import tempfile
from urllib.parse import urlparse

from url_normalize import url_normalize

import magic
import spectra
from django.http import QueryDict
from imagekit.utils import get_cache
from imagekit.models import ProcessedImageField
import hashlib

from openbook_common.utils.model_loaders import get_post_model
from openbook_common.validators import is_valid_hex_color

r = lambda: secrets.randbelow(255)


def normalise_request_data(request_data):
    """
    request.data is a QueryDict if multiform request and dict if JSON request
    This normalises the data
    :param request_data:
    :return:
    """
    if not request_data:
        return {}

    if isinstance(request_data, QueryDict):
        return request_data.dict()
    return {**request_data}


def nomalize_usernames_in_request_data(request_data):
    normalize_list_value_in_request_data(list_name='usernames', request_data=request_data)


def normalize_list_value_in_request_data(list_name, request_data):
    """Checks if a list value is a list. If its a string, splits it and makes it a list"""
    list = request_data.get(list_name, None)
    if isinstance(list, str):
        list = list.split(',')
        list_items_count = len(list)
        if list_items_count == 1 and list[0] == '':
            list = []
        request_data[list_name] = list


def generate_random_hex_color():
    return '#%02X%02X%02X' % (r(), r(), r())


def get_random_pastel_color():
    # Its a random color jeez, we dont need cryptographically secure randomness
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0  # nosec
    r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
    hex_color = '#%02x%02x%02x' % (r, g, b)
    color = spectra.html(hex_color).darken(amount=20)
    return color.hexcode


def delete_file_field(filefield):
    if not filefield:
        return

    try:
        file = filefield.file

    except FileNotFoundError:
        pass

    else:

        if isinstance(filefield.field, ProcessedImageField):
            # ImageKit has a bug where files are cached and not deleted right away
            # https://github.com/matthewwithanm/django-imagekit/issues/229#issuecomment-315690575
            cache = get_cache()
            cache.delete(cache.get(file))

        filefield.storage.delete(file.name)


def sha256sum(filename=None, file=None):
    if filename:
        with open(filename, 'rb', buffering=0) as f:
            return _sha256sum(file=f)
    elif file:
        return _sha256sum(file=file)
    else:
        raise Exception('file or filename are required')


def _sha256sum(file):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    for n in iter(lambda: file.readinto(mv), 0):
        h.update(mv[:n])
    file.seek(0)
    return h.hexdigest()


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    return Post.get_post_id_for_post_with_uuid(post_uuid=post_uuid)


# Same as flutter app
usernames_regexp = re.compile('@[^\s]+')


def extract_usernames_from_string(string):
    usernames = usernames_regexp.findall(string=string)
    return [username[1:] for username in usernames]


hashtags_regexp = re.compile(r'\B#\w*[a-zA-Z]+\w*')


def extract_hashtags_from_string(string):
    hashtags = hashtags_regexp.findall(string=string)
    extracted_hashtags = [hashtag[1:] for hashtag in hashtags]
    return extracted_hashtags


magic = magic.Magic(magic_file='openbook_common/misc/magic.mgc', mime=True)


def get_magic():
    return magic


def write_in_memory_file_to_disk(in_memory_file):
    extension = os.path.splitext(in_memory_file.name)[1]

    tmp_file = tempfile.mkstemp(suffix=extension)
    tmp_file_path = tmp_file[1]
    tmp_file = open(tmp_file_path, 'wb')
    # Was read for the magic headers thing
    tmp_file.write(in_memory_file.read())
    tmp_file.seek(0)
    tmp_file.close()
    return tmp_file


def normalize_url(url, default_scheme='http', scheme=None):
    normalized_url = url_normalize(url, default_scheme=scheme or default_scheme)
    if scheme:
        parsed_url = urlparse(normalized_url)
        if parsed_url.scheme != scheme:
            normalized_url = normalized_url.replace('http://', 'https://')
            parsed_url = urlparse(normalized_url)
            normalized_url = parsed_url.geturl()

    return normalized_url
