class VideoEncodingError(Exception):
    pass


class FFmpegError(VideoEncodingError):
    def __init__(self, *args, **kwargs):
        self.msg = args[0]
        super(VideoEncodingError, self).__init__(*args, **kwargs)


class InvalidTimeError(VideoEncodingError):
    pass
