from rest_framework.exceptions import ValidationError
from rest_framework.fields import URLField, FileField
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.forms import ImageField as DjangoImageField


class FriendlyUrlField(URLField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            if 'https://' not in data and 'http://' not in data:
                data = 'https://' + data
        return data


class RestrictedFileSizeField(FileField):
    """
    Same as FileField, but you can specify:
        * max_upload_size - a number indicating the maximum file size allowed for upload.
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    """

    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop("max_upload_size")

        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data = super().to_internal_value(data=data)

        size = data.size
        if size > self.max_upload_size:
            raise ValidationError(_('Please keep filesize under %s. Current filesize %s' % (
            filesizeformat(self.max_upload_size), filesizeformat(size))
                                    ))

        return data


class RestrictedImageFileSizeField(RestrictedFileSizeField):
    default_error_messages = {
        'invalid_image': _(
            'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'
        ),
    }

    def __init__(self, *args, **kwargs):
        self._DjangoImageField = kwargs.pop('_DjangoImageField', DjangoImageField)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        # Image validation is a bit grungy, so we'll just outright
        # defer to Django's implementation so we don't need to
        # consider it, or treat PIL as a test dependency.
        file_object = super().to_internal_value(data)
        django_field = self._DjangoImageField()
        django_field.error_messages = self.error_messages
        return django_field.clean(file_object)
