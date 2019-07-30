from langdetect import DetectorFactory, detect
from openbook_common.utils.model_loaders import get_language_model
from openbook_translation import strategy
import re

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


def get_supported_translation_language(language_code):
    Language = get_language_model()
    supported_translation_code = strategy.get_supported_translation_language_code(language_code)

    return Language.objects.get(code=supported_translation_code)


def get_first_matched_url_from_text(text):
    match_urls_pattern = re.compile(r"(?i)(http[s]?://|www)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!#*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
    # (http[s]?:\/\/|www)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!#*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+
    # (?:(https?):\/\/|www\.)(?:\([-A-Z0-9+&@#/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#/%=~_|$?!:,.]*\)|[A-Z0-9+&@#/%=~_|$])

    # fully matching (http[s]?://|www)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!#*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+

    result = match_urls_pattern.search(text, re.IGNORECASE)
    print('URLs found:', result)
    if result is not None:
        return result.group()

    return result

