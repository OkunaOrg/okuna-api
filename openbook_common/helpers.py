from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

from openbook_common.utils.model_loaders import get_language_model
from openbook_translation import translation_strategy

# seed the language detector
DetectorFactory.seed = 0


def get_detected_language_code(text):
    try:
        detected_lang = translation_strategy.get_detected_language_code(text)
    except LangDetectException:
        detected_lang = None
    return detected_lang


def get_language_for_text(text):
    language_code = get_detected_language_code(text)
    Language = get_language_model()
    if language_code is not None and Language.objects.filter(code=language_code).exists():
        return Language.objects.get(code=language_code)

    return None


def get_supported_translation_language(language_code):
    Language = get_language_model()
    supported_translation_code = translation_strategy.get_supported_translation_language_code(language_code)

    return Language.objects.get(code=supported_translation_code)
