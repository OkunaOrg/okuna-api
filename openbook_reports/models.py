from django.db import models
from openbook_auth.models import User
from openbook_posts.models import Post, PostComment
from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from enum import Enum
from django.conf import settings
from django.utils import timezone

class ReportCategory(models.Model):
    name = models.CharField(_('name'), max_length=settings.REPORT_CATEGORY_NAME_MAX_LENGTH, blank=False, null=False,
                            unique=True)
    title = models.CharField(_('title'), max_length=settings.REPORT_CATEGORY_TITLE_MAX_LENGTH, blank=False, null=False)
    description = models.CharField(_('description'), max_length=settings.REPORT_CATEGORY_DESCRIPTION_MAX_LENGTH,
                                   blank=False,
                                   null=True)
    created = models.DateTimeField(editable=False)

    @classmethod
    def create_category(cls, name, title=None, description=None):
        category = cls.objects.create(name=name, title=title, description=description)

        return category

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(ReportCategory, self).save(*args, **kwargs)


class AbstractReport(models.Model):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    REJECTED = 'REJECTED'
    RESOLVED = 'RESOLVED'

    REPORT_STATUS_CHOICES = (
        (PENDING, 'PENDING'),
        (CONFIRMED, 'CONFIRMED'),
        (REJECTED, 'REJECTED'),
        (RESOLVED, 'RESOLVED'),
    )

    category = models.ForeignKey(ReportCategory, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=settings.REPORT_STATUS_MAX_LENGTH, choices=REPORT_STATUS_CHOICES,
                              null=True, blank=False, default=PENDING)
    comment = models.CharField(max_length=settings.REPORT_COMMENT_MAX_LENGTH, null=True, blank=True)
    created = models.DateTimeField(editable=False)

    class Meta:
        abstract = True

    def check_report_status_is_pending(self):
        if not self.status == self.PENDING:
            raise ValidationError(
                _('Cannot change status of report'),
            )

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(AbstractReport, self).save(*args, **kwargs)


class PostReport(AbstractReport):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reports')

    class Meta:
        unique_together = ('post', 'reporter')

    @classmethod
    def create_report(cls, post, reporter, category, status=AbstractReport.PENDING, comment=None):
        return PostReport.objects.create(post=post, reporter=reporter, category=category,
                                         status=status, comment=comment)

    @classmethod
    def check_report_status_is_pending_for_report_with_id(cls, report_id):
        report = PostReport.objects.get(pk=report_id)
        report.check_report_status_is_pending()


class PostCommentReport(AbstractReport):
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_reports')

    class Meta:
        unique_together = ('post_comment', 'reporter')

    @classmethod
    def create_comment_report(cls, post_comment, reporter, category, comment):
        return PostCommentReport.objects.create(post_comment=post_comment, reporter=reporter,
                                                category=category, comment=comment)

    @classmethod
    def check_report_status_is_pending_for_report_with_id(cls, report_id):
        report = PostCommentReport.objects.get(pk=report_id)
        report.check_report_status_is_pending()
