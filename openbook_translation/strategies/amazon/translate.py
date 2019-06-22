from openbook_translation.strategies.base import BaseTranslationStrategy
from django.conf import settings
from langdetect import DetectorFactory, detect
import boto3

# seed the language detector
DetectorFactory.seed = 0

class AmazonTranslate(BaseTranslationStrategy):

    client = boto3.client(service_name='translate', region_name=settings., use_ssl=True)

    def get_detected_language_code(self, text):
        # amazons translate API codes as stored in the languages.json are slightly different
        # for chinese (zh) and chinese traditional (zh-TW)

        detected_language = detect(text)
        if detected_language is 'zh-cn':
            detected_language = 'zh'
        if detected_language is 'zh-tw':
            detected_language = 'zh-TW'

        return detected_language

    def translate_text(self, text, source_language_code, target_language_code):
        result = self.client.translate_text(Text="Hello, World", SourceLanguageCode="en", TargetLanguageCode="de")


