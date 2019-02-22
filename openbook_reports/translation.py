from modeltranslation.translator import translator, TranslationOptions

from openbook_reports.models import ReportCategory


class ReportCategoryTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


translator.register(ReportCategory, ReportCategoryTranslationOptions)
