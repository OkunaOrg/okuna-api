from modeltranslation.translator import translator, TranslationOptions

from openbook_tags.models import Tag


class TagTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


translator.register(Tag, TagTranslationOptions)
