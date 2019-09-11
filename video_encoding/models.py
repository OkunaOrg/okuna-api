from os.path import splitext

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .fields import VideoField
from .manager import FormatManager


def upload_format_to(i, f):
    return 'formats/%s/%s%s' % (
        i.format,
        splitext(getattr(i.video, i.field_name).name)[0],  # keep path
        splitext(f)[1].lower())


class Format(models.Model):
    object_id = models.PositiveIntegerField(
        editable=False,
    )
    content_type = models.ForeignKey(
        ContentType,
        editable=False,
        on_delete=models.CASCADE
    )
    video = GenericForeignKey()
    field_name = models.CharField(
        max_length=255,
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
        editable=False,
        verbose_name=_("Progress"),
    )
    format = models.CharField(
        max_length=255,
        editable=False,
        verbose_name=_("Format"),
    )
    file = VideoField(
        duration_field='duration',
        editable=False,
        max_length=2048,
        upload_to=upload_format_to,
        verbose_name=_("File"),
        width_field='width', height_field='height',
    )
    width = models.PositiveIntegerField(
        editable=False,
        null=True,
        verbose_name=_("Width"),
    )
    height = models.PositiveIntegerField(
        editable=False,
        null=True,
        verbose_name=_("Height"),
    )
    duration = models.PositiveIntegerField(
        editable=False,
        null=True,
        verbose_name=_("Duration (s)"),
    )

    objects = FormatManager()

    class Meta:
        verbose_name = _("Format")
        verbose_name_plural = _("Formats")

    def __str__(self):
        return '{} ({:d}%)'.format(self.file.name, self.progress)

    def unicode(self):
        return self.__str__()

    def update_progress(self, percent, commit=True):
        if 0 > percent > 100:
            raise ValueError("Invalid percent value.")

        self.progress = percent
        if commit:
            self.save()

    def reset_progress(self, commit=True):
        self.percent = 0
        if commit:
            self.save()
