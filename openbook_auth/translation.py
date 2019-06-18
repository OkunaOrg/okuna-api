from modeltranslation.translator import translator, TranslationOptions
from openbook_auth.models import UserLanguage


class UserLanguageTranslationOptions(TranslationOptions):
    fields = ('name',)


translator.register(UserLanguage, UserLanguageTranslationOptions)