from rest_framework.exceptions import ValidationError
from openbook_reports.models import ReportCategory, PostReport, PostCommentReport
from django.utils.translation import ugettext_lazy as _


def is_valid_report_category(category_name):
    if not ReportCategory.objects.filter(name=category_name).exists():
        raise ValidationError(
            _('This is not a valid report category.'),
        )


def report_id_exists(report_id):
    if not PostReport.objects.filter(pk=report_id).exists():
        raise ValidationError(
            _('This is not a valid report id.'),
        )


def comment_report_id_exsits(report_id):
    if not PostCommentReport.objects.filter(pk=report_id).exists():
        raise ValidationError(
            _('This is not a valid post comment report id.'),
        )