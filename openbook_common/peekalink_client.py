import requests
from django.conf import settings


class PeekalinkError(Exception):
    """Base class for other exceptions"""
    pass


class PeekalinkUnexpectedResponseError(PeekalinkError):
    def __init__(self,
                 message="Peekalink responded unexpectedly. Please verify you are using the latest client or contact support."):
        self.message = message
        super().__init__(self.message)


class PeekalinkClient:
    default_timeout = (3, 10)

    def __init__(self, api_key, default_timeout=None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'X-API-Key': self.api_key})

        if default_timeout:
            self.default_timeout = default_timeout

    def peek(self, link: str, language_code=None, timeout=None):
        if not timeout:
            timeout = self.default_timeout

        headers = {}

        if language_code:
            headers['Accept-Language'] = language_code

        request_data = {
            'link': link
        }

        response = self.session.post(
            'https://api.peekalink.io/',
            headers=headers,
            data=request_data,
            timeout=timeout if timeout else self.default_timeout
        )

        response.raise_for_status()

        return response.json()

    def is_peekable(self, link: str, language_code=None, timeout=None):
        if not timeout:
            timeout = self.default_timeout

        headers = {}

        if language_code:
            headers['Accept-Language'] = language_code

        request_data = {
            'link': link
        }

        response = self.session.post(
            'https://api.peekalink.io/is-peekable/',
            headers=headers,
            data=request_data,
            timeout=timeout if timeout else self.default_timeout
        )

        response.raise_for_status()

        response_data = response.json()

        if not response_data['isPeekable']:
            raise PeekalinkUnexpectedResponseError()

        return response_data['isPeekable']


peekalink_client = PeekalinkClient(api_key=settings.PEEKALINK_API_KEY)
