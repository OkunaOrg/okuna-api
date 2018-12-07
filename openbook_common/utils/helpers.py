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
