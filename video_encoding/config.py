from appconf import AppConf
from django.conf import settings  # NOQA


class VideoEncodingAppConf(AppConf):
    THREADS = 1
    PROGRESS_UPDATE = 30
    BACKEND = 'video_encoding.backends.ffmpeg.FFmpegBackend'
    BACKEND_PARAMS = {}
    FORMATS = {
        'FFmpeg': [
            {
                'name': 'webm_sd',
                'extension': 'webm',
                'params': [
                    '-b:v', '1000k', '-maxrate', '1000k', '-bufsize', '2000k',
                    '-codec:v', 'libvpx', '-r', '30',
                    '-vf', 'scale=-1:480', '-qmin', '10', '-qmax', '42',
                    '-codec:a', 'libvorbis', '-b:a', '128k', '-f', 'webm',
                ],
            },
            {
                'name': 'webm_hd',
                'extension': 'webm',
                'params': [
                    '-codec:v', 'libvpx',
                    '-b:v', '3000k', '-maxrate', '3000k', '-bufsize', '6000k',
                    '-vf', 'scale=-1:720', '-qmin', '11', '-qmax', '51',
                    '-acodec', 'libvorbis', '-b:a', '128k', '-f', 'webm',
                ],
            },
            {
                'name': 'mp4_sd',
                'extension': 'mp4',
                'params': [
                    '-codec:v', 'libx264', '-crf', '20', '-preset', 'medium',
                    '-b:v', '1000k', '-maxrate', '1000k', '-bufsize', '2000k',
                    '-vf', 'scale=-2:480',  # http://superuser.com/a/776254
                    '-codec:a', 'aac', '-b:a', '128k', '-strict', '-2',
                ],
            },
            {
                'name': 'mp4_hd',
                'extension': 'mp4',
                'params': [
                    '-codec:v', 'libx264', '-crf', '20', '-preset', 'medium',
                    '-b:v', '3000k', '-maxrate', '3000k', '-bufsize', '6000k',
                    '-vf', 'scale=-2:720',
                    '-codec:a', 'aac', '-b:a', '128k', '-strict', '-2',
                ],
            },
        ]
    }
