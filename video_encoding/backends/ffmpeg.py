import json
import locale
import logging
import os
import re
import tempfile
from subprocess import PIPE, Popen

import six
from django.core import checks

from .. import exceptions
from ..compat import which
from ..config import settings
from .base import BaseEncodingBackend

logger = logging.getLogger(__name__)
RE_TIMECODE = re.compile(r'time=(\d+:\d+:\d+.\d+) ')

console_encoding = locale.getdefaultlocale()[1] or 'UTF-8'


class FFmpegBackend(BaseEncodingBackend):
    name = 'FFmpeg'

    def __init__(self):

        # This will fix errors in tests
        self.params = [
            '-threads',
            str(settings.VIDEO_ENCODING_THREADS),
            '-y',  # overwrite temporary created file
            '-strict', '-2',  # support aac codec (which is experimental)
        ]

        self.ffmpeg_path = getattr(
            settings, 'VIDEO_ENCODING_FFMPEG_PATH', which('ffmpeg'))
        self.ffprobe_path = getattr(
            settings, 'VIDEO_ENCODING_FFPROBE_PATH', which('ffprobe'))

        if not self.ffmpeg_path:
            raise exceptions.FFmpegError("ffmpeg binary not found: {}".format(
                self.ffmpeg_path or ''))

        if not self.ffprobe_path:
            raise exceptions.FFmpegError("ffprobe binary not found: {}".format(
                self.ffmpeg_path or ''))

    @classmethod
    def check(cls):
        errors = super(FFmpegBackend, cls).check()
        try:
            FFmpegBackend()
        except exceptions.FFmpegError as e:
            errors.append(checks.Error(
                e.msg,
                hint="Please install ffmpeg.",
                obj=cls,
                id='video_conversion.E001',
            ))
        return errors

    def _spawn(self, cmds):
        try:
            return Popen(
                cmds, shell=False,
                stdin=PIPE, stdout=PIPE, stderr=PIPE,
                close_fds=True,
            )
        except OSError as e:
            raise six.raise_from(
                exceptions.FFmpegError('Error while running ffmpeg binary'), e)

    def _check_returncode(self, process):
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise exceptions.FFmpegError("`{}` exited with code {:d}".format(
                ' '.join(process.args), process.returncode))
        self.stdout = stdout.decode(console_encoding)
        self.stderr = stderr.decode(console_encoding)
        return self.stdout, self.stderr

    # TODO reduce complexity
    def encode(self, source_path, target_path, params):  # NOQA: C901
        """
        Encodes a video to a specified file. All encoder specific options
        are passed in using `params`.
        """
        total_time = self.get_media_info(source_path)['duration']

        cmds = [self.ffmpeg_path, '-i', source_path]
        cmds.extend(self.params)
        cmds.extend(params)
        cmds.extend([target_path])

        process = self._spawn(cmds)

        buf = output = ''
        # update progress
        while True:
            # any more data?
            out = process.stderr.read(10)
            if not out:
                break

            out = out.decode(console_encoding)
            output += out
            buf += out

            try:
                line, buf = buf.split('\r', 1)
            except ValueError:
                continue

            try:
                time_str = RE_TIMECODE.findall(line)[0]
            except IndexError:
                continue

            # convert progress to percent
            time = 0
            for part in time_str.split(':'):
                time = 60 * time + float(part)

            percent = time / total_time
            logger.debug('yield {}%'.format(percent))
            yield percent

        if os.path.getsize(target_path) == 0:
            raise exceptions.FFmpegError("File size of generated file is 0")

        # wait for process to exit
        self._check_returncode(process)

        logger.debug(output)
        if not output:
            raise exceptions.FFmpegError("No output from FFmpeg.")

        yield 100

    def _parse_media_info(self, data):
        media_info = json.loads(data)
        media_info['video'] = [stream for stream in media_info['streams']
                               if stream['codec_type'] == 'video']
        media_info['audio'] = [stream for stream in media_info['streams']
                               if stream['codec_type'] == 'audio']
        media_info['subtitle'] = [stream for stream in media_info['streams']
                                  if stream['codec_type'] == 'subtitle']
        del media_info['streams']
        return media_info

    def get_media_info(self, video_path):
        """
        Returns information about the given video as dict.
        """
        cmds = [self.ffprobe_path, '-i', video_path]
        cmds.extend(['-print_format', 'json'])
        cmds.extend(['-show_format', '-show_streams'])

        process = self._spawn(cmds)
        stdout, __ = self._check_returncode(process)

        media_info = self._parse_media_info(stdout)

        return {
            'duration': float(media_info['format']['duration']),
            'width': int(media_info['video'][0]['width']),
            'height': int(media_info['video'][0]['height']),
        }

    def get_thumbnail(self, video_path, at_time=0.5):
        """
        Extracts an image of a video and returns its path.

        If the requested thumbnail is not within the duration of the video
        an `InvalidTimeError` is thrown.
        """
        filename = os.path.basename(video_path)
        filename, __ = os.path.splitext(filename)
        _, image_path = tempfile.mkstemp(suffix='_{}.jpg'.format(filename))

        video_duration = self.get_media_info(video_path)['duration']
        if at_time > video_duration:
            raise exceptions.InvalidTimeError()
        thumbnail_time = at_time

        cmds = [self.ffmpeg_path, '-i', video_path, '-vframes', '1']
        cmds.extend(['-ss', str(thumbnail_time), '-y', image_path])

        process = self._spawn(cmds)
        self._check_returncode(process)

        if not os.path.getsize(image_path):
            # we somehow failed to generate thumbnail
            os.unlink(image_path)
            raise exceptions.InvalidTimeError()

        return image_path
