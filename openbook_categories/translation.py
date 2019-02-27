from modeltranslation.translator import translator, TranslationOptions

from openbook_categories.models import Category


class CategoryTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


translator.register(Category, CategoryTranslationOptions)
