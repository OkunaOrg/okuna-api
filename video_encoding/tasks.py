import os
import tempfile

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.files import File

from .backends import get_backend
from .config import settings
from .exceptions import VideoEncodingError
from .fields import VideoField
from .models import Format


def convert_all_videos(app_label, model_name, object_pk):
    """
    Automatically converts all videos of a given instance.
    """
    # get instance
    Model = apps.get_model(app_label=app_label, model_name=model_name)
    instance = Model.objects.get(pk=object_pk)

    # search for `VideoFields`
    fields = instance._meta.fields
    for field in fields:
        if isinstance(field, VideoField):
            if not getattr(instance, field.name):
                # ignore empty fields
                continue

            # trigger conversion
            fieldfile = getattr(instance, field.name)
            convert_video(fieldfile)


def convert_video(fieldfile, force=False):
    """
    Converts a given video file into all defined formats.
    """
    instance = fieldfile.instance
    field = fieldfile.field

    filename = os.path.basename(fieldfile.path)
    source_path = fieldfile.path

    encoding_backend = get_backend()

    for options in settings.VIDEO_ENCODING_FORMATS[encoding_backend.name]:
        video_format, created = Format.objects.get_or_create(
            object_id=instance.pk,
            content_type=ContentType.objects.get_for_model(instance),
            field_name=field.name, format=options['name'])

        # do not reencode if not requested
        if video_format.file and not force:
            continue
        else:
            # set progress to 0
            video_format.reset_progress()

        # TODO do not upscale videos

        _, target_path = tempfile.mkstemp(
            suffix='_{name}.{extension}'.format(**options))

        try:
            encoding = encoding_backend.encode(
                source_path, target_path, options['params'])
            while encoding:
                try:
                    progress = next(encoding)
                except StopIteration:
                    break
                video_format.update_progress(progress)
        except VideoEncodingError:
            # TODO handle with more care
            video_format.delete()
            os.remove(target_path)
            continue

        # save encoded file
        video_format.file.save(
            '{filename}_{name}.{extension}'.format(filename=filename,
                                                   **options),
            File(open(target_path, mode='rb')))

        video_format.update_progress(100)  # now we are ready

        # remove temporary file
        os.remove(target_path)
