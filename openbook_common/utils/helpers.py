import secrets

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import QueryDict
from imagekit.utils import get_cache
from imagekit.models import ProcessedImageField
import hashlib

from openbook_common.utils.model_loaders import get_post_model

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