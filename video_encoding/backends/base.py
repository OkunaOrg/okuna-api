import abc

import six


class BaseEncodingBackend(six.with_metaclass(abc.ABCMeta)):
    # used as key to get all defined formats from `VIDEO_ENCODING_FORMATS`
    name = 'undefined'

    @classmethod
    def check(cls):
        return []

    @abc.abstractmethod
    def encode(self, source_path, target_path, params):  # pragma: no cover
        """
        Encodes a video to a specified file. All encoder specific options
        are passed in using `params`.
        """
        pass

    @abc.abstractmethod
    def get_media_info(self, video_path):  # pragma: no cover
        """
        Returns duration, width and height of the video as dict.
        """
        pass

    @abc.abstractmethod
    def get_thumbnail(self, video_path):  # pragma: no cover
        """
        Extracts an image of a video and returns its path.

        If the requested thumbnail is not within the duration of the video
        an `InvalidTimeError` is thrown.
        """
        pass
