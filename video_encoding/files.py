import os

from django.core.files import File

from video_encoding.utils import get_fieldfile_local_path
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

            local_path, local_tmp_file = get_fieldfile_local_path(fieldfile=self)

            info_cache = encoding_backend.get_media_info(local_path)

            if local_tmp_file:
                os.unlink(local_tmp_file.name)
                local_tmp_file.close()

            self._info_cache = info_cache

        return self._info_cache
