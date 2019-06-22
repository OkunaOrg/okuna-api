from abc import ABC, abstractmethod

from django.core.exceptions import ImproperlyConfigured


class InvalidTranslationStrategyError(ImproperlyConfigured):
    pass


class BaseTranslationStrategy(ABC):

    def __init__(self, params):
        super().__init__()

    @abstractmethod
    def get_detected_language_code(self, text):
        pass

    @abstractmethod
    def translate_text(self, *args, **kwargs):
        pass

