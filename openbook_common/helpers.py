from langdetect import DetectorFactory, detect


from openbook_common.utils.model_loaders import get_language_model

# seed the language detector
DetectorFactory.seed = 0


def get_detected_language_code(text):
    # amazons translate API codes as stored in the languages.json are slightly different
    # for chinese (zh) and chinese traditional (zh-TW)

    detected_language = detect(text)
    if detected_language is 'zh-cn':
        detected_language = 'zh'
    if detected_language is 'zh-tw':
        detected_language = 'zh-TW'

    return detected_language


def get_language_for_text(text):
    language_code = get_detected_language_code(text)
    Language = get_language_model()
    if Language.objects.filter(code=language_code).exists():
        return Language.objects.get(code=language_code)

    return None
