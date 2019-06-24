from rest_framework import serializers
from openbook_common.validators import language_code_exists
from openbook_translation import strategy


class TranslateTextSerializer(serializers.Serializer):
    source_language_code = serializers.CharField(required=True,
                                                 max_length=strategy.text_max_length,
                                                 validators=[language_code_exists],
                                                 allow_blank=False)
    target_language_code = serializers.CharField(required=True,
                                                 max_length=strategy.text_max_length,
                                                 validators=[language_code_exists],
                                                 allow_blank=False)
    text = serializers.CharField(required=True)
