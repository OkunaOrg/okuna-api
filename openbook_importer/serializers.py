from rest_framework import serializers


class ZipfileSerializer(serializers.Serializer):

    serializers.FileField(max_length=20, required=True,
                          allow_empty_file=False)
