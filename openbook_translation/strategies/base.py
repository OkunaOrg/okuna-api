from abc import ABC, abstractmethod


class BaseTranslationStrategy(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_detected_language_code(self, text):
        pass

    @abstractmethod
    def translate_text(self, *args, **kwargs):
        pass

