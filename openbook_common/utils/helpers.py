from django.http import QueryDict


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
    usernames = request_data.get('usernames', None)
    if isinstance(usernames, str):
        usernames = usernames.split(',')
        usernames_count = len(usernames)
        if usernames_count == 1 and usernames[0] == '':
            usernames = []
        request_data['usernames'] = usernames
