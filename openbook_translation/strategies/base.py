from abc import ABC, abstractmethod

from django.core.exceptions import ImproperlyConfigured, ValidationError


class InvalidTranslationStrategyError(ImproperlyConfigured):
    pass


class MaxTextLengthExceededError(ValidationError):
    pass


class TranslationClientError(Exception):
    pass


class UnsupportedLanguagePairException(Exception):
    pass


class BaseTranslationStrategy(ABC):

    def __init__(self, params):
        if 'TEXT_MAX_LENGTH' in params:
            self.text_max_length = int(params.pop('TEXT_MAX_LENGTH'))
            self.default_translation_language_code = params.pop('DEFAULT_TRANSLATION_LANGUAGE_CODE')
        super().__init__()

    @abstractmethod
    def get_detected_language_code(self, text):
        pass

    @abstractmethod
    def get_supported_translation_language_code(self, language_code):
        pass

    @abstractmethod
    def translate_text(self, *args, **kwargs):
        pass

