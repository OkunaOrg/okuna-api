from rest_framework import serializers
from openbook_importer.models import Import


class ZipfileSerializer(serializers.Serializer):

    file = serializers.FileField(max_length=1000000000, required=True,
                                 allow_empty_file=False)


class ImportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Import
        fields = (
            'uuid',
            'created',
            'posts'
        )
