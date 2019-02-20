from django.http import QueryDict
import secrets
from imagekit.utils import get_cache

r = lambda: secrets.randbelow(255)


def normalise_request_data(request_data):
    """
    request.data is a QueryDict if multiform request and dict if JSON request
    This normalises the data
    :param request_data:
    :return:
    """
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


def delete_image_kit_image_field(image_kit_field):
    # ImageKit has a bug where files are cached and not deleted right away
    # https://github.com/matthewwithanm/django-imagekit/issues/229#issuecomment-315690575

    if not image_kit_field:
        return

    try:
        file = image_kit_field.file
    except FileNotFoundError:
        pass
    else:
        cache = get_cache()
        cache.delete(cache.get(file))
        image_kit_field.storage.delete(file.name)

    image_kit_field.delete()
