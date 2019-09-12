from django.db.models.fields.files import (FieldFile, ImageField,
                                           ImageFileDescriptor)
from django.utils.translation import ugettext as _

from .backends import get_backend_class
from .files import VideoFile


class VideoFileDescriptor(ImageFileDescriptor):
    pass


class VideoFieldFile(VideoFile, FieldFile):
    def delete(self, save=True):
        # Clear the video info cache
        if hasattr(self, '_info_cache'):
            del self._info_cache
        super(VideoFieldFile, self).delete(save=save)


class VideoField(ImageField):
    attr_class = VideoFieldFile
    descriptor_class = VideoFileDescriptor
    description = _("Video")

    def __init__(self, verbose_name=None, name=None, duration_field=None,
                 **kwargs):
        self.duration_field = duration_field
        super(VideoField, self).__init__(verbose_name, name, **kwargs)

    def check(self, **kwargs):
        errors = super(ImageField, self).check(**kwargs)
        errors.extend(self._check_backend())
        return errors

    def _check_backend(self):
        backend = get_backend_class()
        return backend.check()

    def to_python(self, data):
        # use FileField method
        return super(ImageField, self).to_python(data)

    def update_dimension_fields(self, instance, force=False, *args, **kwargs):
        _file = getattr(instance, self.attname)

        # we need a real file
        if not _file._committed:
            return

        # write `width` and `height`
        super(VideoField, self).update_dimension_fields(instance, force,
                                                        *args, **kwargs)
        if not self.duration_field:
            return

        # Nothing to update if we have no file and not being forced to update.
        if not _file and not force:
            return
        if getattr(instance, self.duration_field) and not force:
            return

        # get duration if file is defined
        duration = _file.duration if _file else None

        # update duration
        setattr(instance, self.duration_field, duration)

    def formfield(self, **kwargs):
        # use normal FileFieldWidget for now
        return super(ImageField, self).formfield(**kwargs)
