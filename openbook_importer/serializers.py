from rest_framework import serializers
from openbook_importer.models import Import


class ZipfileSerializer(serializers.Serializer):

    serializers.FileField(max_length=20, required=True,
                          allow_empty_file=False)


class ImportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Import
        fields = (
            'uuid',
            'created',
            'posts'
        )
