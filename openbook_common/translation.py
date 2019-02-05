from modeltranslation.translator import translator, TranslationOptions

from openbook_common.models import Emoji, EmojiGroup, Badge


class EmojiGroupTranslationOptions(TranslationOptions):
    fields = ('keyword',)


translator.register(EmojiGroup, EmojiGroupTranslationOptions)


class EmojiTranslationOptions(TranslationOptions):
    fields = ('keyword',)


translator.register(Emoji, EmojiTranslationOptions)


class BadgeTranslationOptions(TranslationOptions):
    fields = ('keyword_description',)


translator.register(Badge, BadgeTranslationOptions)
