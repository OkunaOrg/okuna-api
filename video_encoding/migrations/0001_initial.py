# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import video_encoding.fields
import video_encoding.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Format',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('object_id', models.PositiveIntegerField()),
                ('field_name', models.CharField(max_length=255)),
                ('progress', models.PositiveSmallIntegerField(verbose_name='Progress', default=0)),
                ('format', models.CharField(verbose_name='Format', max_length=255)),
                ('file', video_encoding.fields.VideoField(height_field='height', verbose_name='File', width_field='width', max_length=2048, upload_to=video_encoding.models.upload_format_to)),
                ('width', models.PositiveIntegerField(verbose_name='Width', null=True)),
                ('height', models.PositiveIntegerField(verbose_name='Height', null=True)),
                ('duration', models.PositiveIntegerField(verbose_name='Duration (s)', null=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Format',
                'verbose_name_plural': 'Formats',
            },
        ),
    ]
