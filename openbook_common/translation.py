from modeltranslation.translator import translator, TranslationOptions

from openbook_common.models import Emoji, EmojiGroup


class EmojiGroupTranslationOptions(TranslationOptions):
    fields = ('keyword',)


translator.register(EmojiGroup, EmojiGroupTranslationOptions)


class EmojiTranslationOptions(TranslationOptions):
    fields = ('keyword',)


translator.register(Emoji, EmojiTranslationOptions)
