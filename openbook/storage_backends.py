from botocore.config import Config
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class S3StaticStorage(S3Boto3Storage):
    location = settings.AWS_STATIC_LOCATION

    def __init__(self, *args, **kwargs):
        self.config = Config(s3={'addressing_style': self.addressing_style,
                                 'use_accelerate_endpoint': True},
                             signature_version=self.signature_version)
        super().__init__(*args, **kwargs)


class S3PublicMediaStorage(S3Boto3Storage):
    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    file_overwrite = False

    def __init__(self, *args, **kwargs):
        self.config = Config(s3={'addressing_style': self.addressing_style,
                                 'use_accelerate_endpoint': True},
                             signature_version=self.signature_version)
        super().__init__(*args, **kwargs)


class S3PrivateMediaStorage(S3Boto3Storage):
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False

    def __init__(self, *args, **kwargs):
        self.config = Config(s3={'addressing_style': self.addressing_style,
                                 'use_accelerate_endpoint': True},
                             signature_version=self.signature_version)
        super().__init__(*args, **kwargs)
