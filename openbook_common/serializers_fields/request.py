from rest_framework.fields import URLField


class FriendlyUrlField(URLField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            if 'https://' not in data and 'http://' not in data:
                data = 'https://' + data
        return data
