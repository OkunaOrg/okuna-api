from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext as _

from openbook_common.responses import ApiMessageResponse
from openbook_translation.serializers import TranslateTextSerializer

from openbook_translation import strategy
from openbook_translation.strategies.base import TranslationClientError, MaxTextLengthExceededError, \
    UnsupportedLanguagePairException


class TranslateText(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = TranslateTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        source_language_code = data.get('source_language_code')
        target_language_code = data.get('target_language_code')
        text = data.get('text')

        try:
            translated_result = strategy.translate_text(
                source_language_code=source_language_code,
                target_language_code=target_language_code,
                text=text
            )
        except UnsupportedLanguagePairException:
            return ApiMessageResponse(_('Translation pair is not supported by client.'),
                                      status=status.HTTP_400_BAD_REQUEST)
        except TranslationClientError:
            return ApiMessageResponse(_('Translation service returned an error'),
                                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except MaxTextLengthExceededError:
            return ApiMessageResponse(_('Max length of translation text exceeded.'),
                                      status=status.HTTP_400_BAD_REQUEST)

        return Response(translated_result, status=status.HTTP_200_OK)
