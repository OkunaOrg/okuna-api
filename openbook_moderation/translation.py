from modeltranslation.translator import translator, TranslationOptions
from openbook_moderation.models import ModerationCategory


class ModerationCategoryTranslationOptions(TranslationOptions):
    fields = ('description', 'title')


translator.register(ModerationCategory, ModerationCategoryTranslationOptions)
