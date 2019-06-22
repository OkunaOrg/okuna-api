from langdetect import DetectorFactory, detect
from openbook_common.utils.model_loaders import get_language_model
from openbook_translation import strategy

# seed the language detector
DetectorFactory.seed = 0


def get_detected_language_code(text):
    return strategy.get_detected_language_code(text)


def get_language_for_text(text):
    language_code = get_detected_language_code(text)
    Language = get_language_model()
    if Language.objects.filter(code=language_code).exists():
        return Language.objects.get(code=language_code)

    return None
