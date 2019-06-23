from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from openbook_translation.serializers import TranslateTextSerializer

from openbook_translation import strategy


class TranslateText(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = TranslateTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        source_language_code = data.get('source_language_code')
        target_language_code = data.get('target_language_code')
        text = data.get('text')

        translated_result = strategy.translate_text(
            source_language_code=source_language_code,
            target_language_code=target_language_code,
            text=text
        )

        return Response(translated_result, status=status.HTTP_200_OK)
