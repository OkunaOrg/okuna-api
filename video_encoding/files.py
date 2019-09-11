import os

from django.core.files import File

from .backends import get_backend


class VideoFile(File):
    """
    A mixin for use alongside django.core.files.base.File, which provides
    additional features for dealing with videos.
    """

    def _get_width(self):
        """
        Returns video width in pixels.
        """
        return self._get_video_info().get('width', 0)

    width = property(_get_width)

    def _get_height(self):
        """
        Returns video height in pixels.
        """
        return self._get_video_info().get('height', 0)

    height = property(_get_height)

    def _get_duration(self):
        """
        Returns duration in seconds.
        """
        return self._get_video_info().get('duration', 0)

    duration = property(_get_duration)

    def _get_video_info(self):
        """
        Returns basic information about the video as dictionary.
        """
        if not hasattr(self, '_info_cache'):
            encoding_backend = get_backend()

            if hasattr(self, 'file'):
                # Its an actual file
                try:
                    path = os.path.abspath(self.path)
                except AttributeError:
                    path = os.path.abspath(self.name)

                info_cache = encoding_backend.get_media_info(path)
            else:
                # Its not an actual file, so assume storage abstraction
                storage_path = getattr(self, 'path', self.name)
                if not hasattr(self, 'storage'):
                    raise Exception(
                        'VideoFile uses storages yet has no self.storage'
                    )

                storage = self.storage

                try:
                    # If its a storage with file system implementation
                    storage_local_path = storage.path(storage_path)
                except NotImplementedError:
                    storage_local_path = storage.url(storage_path)

                info_cache = encoding_backend.get_media_info(storage_local_path)

            self._info_cache = info_cache

        return self._info_cache
