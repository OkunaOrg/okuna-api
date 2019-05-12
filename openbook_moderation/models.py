from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.
from django.utils import timezone

from openbook_auth.models import User


class ModerationCategory(models.Model):
    name = models.CharField(_('name'), max_length=32, blank=False, null=False)
    title = models.CharField(_('title'), max_length=32, blank=False, null=False)
    description = models.CharField(_('description'), max_length=255, blank=False, null=False)
    created = models.DateTimeField(editable=False, db_index=True)

    SEVERITY_CRITICAL = 'C'
    SEVERITY_HIGH = 'H'
    SEVERITY_MEDIUM = 'M'
    SEVERITY_LOW = 'L'
    SEVERITIES = (
        (SEVERITY_CRITICAL, 'Critical'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_LOW, 'Low'),
    )

    severity = models.CharField(max_length=5, choices=SEVERITIES)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id and not self.created:
            self.created = timezone.now()

        return super(ModerationCategory, self).save(*args, **kwargs)


class ModeratedObject(models.Model):
    description = models.CharField(_('description'), max_length=settings.MODERATED_OBJECT_DESCRIPTION_MAX_LENGTH,
                                   blank=False, null=True)

    approved = models.BooleanField(_('approved'), default=False,
                                   blank=False, null=False)
    verified = models.BooleanField(_('verified'), default=False,
                                   blank=False, null=False)
    submitted = models.BooleanField(_('submitted'), default=False,
                                    blank=False, null=False)

    OBJECT_TYPE_POST = 'P'
    OBJECT_TYPE_POST_COMMENT = 'PC'
    OBJECT_TYPE_COMMUNITY = 'C'
    OBJECT_TYPE_USER = 'U'
    OBJECT_TYPE_MODERATED_OBJECT = 'MO'
    OBJECT_TYPES = (
        (OBJECT_TYPE_POST, 'Post'),
        (OBJECT_TYPE_POST_COMMENT, 'Post Comment'),
        (OBJECT_TYPE_COMMUNITY, 'Community'),
        (OBJECT_TYPE_USER, 'User'),
        (OBJECT_TYPE_MODERATED_OBJECT, 'MO'),
    )

    object_type = models.CharField(max_length=5, choices=OBJECT_TYPES)

    # Generic relation types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    @classmethod
    def create_moderated_object(cls, type, content_object):
        return cls.objects.create(notification_type=type, content_object=content_object)


class ModerationReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_reports')
    overview = models.ForeignKey(ModeratedObject, on_delete=models.CASCADE, related_name='reports')
    category = models.ForeignKey(ModerationCategory, on_delete=models.CASCADE, related_name='reports')
    description = models.CharField(_('description'), max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH,
                                   blank=False, null=True)


class ModerationPenalty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_penalties')
    duration = models.DateTimeField(editable=False)
    moderated_object = models.ForeignKey(ModeratedObject, on_delete=models.CASCADE, related_name='penalties')

    TYPE_SUSPENSION = 'S'

    TYPES = (
        (TYPE_SUSPENSION, 'Suspension'),
    )


class ModeratedObjectLog(models.Model):
    LOG_TYPE_DESCRIPTION_CHANGED = 'DC'
    LOG_TYPE_APPROVED_CHANGED = 'AC'
    LOG_TYPE_TYPE_CHANGED = 'TC'
    LOG_TYPE_SUBMITTED_CHANGED = 'SC'
    LOG_TYPE_VERIFIED_CHANGED = 'VC'
    LOG_TYPE_CATEGORY_CHANGED = 'CC'

    LOG_TYPES = (
        (LOG_TYPE_DESCRIPTION_CHANGED, 'Description Changed'),
        (LOG_TYPE_APPROVED_CHANGED, 'Approved Changed'),
        (LOG_TYPE_TYPE_CHANGED, 'Type Changed'),
        (LOG_TYPE_SUBMITTED_CHANGED, 'Submitted Changed'),
        (LOG_TYPE_VERIFIED_CHANGED, 'Verified Changed'),
        (LOG_TYPE_CATEGORY_CHANGED, 'Category Changed'),
    )

    log_type = models.CharField(max_length=5, choices=LOG_TYPES)

    # Generic relation types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    moderated_object = models.ForeignKey(ModeratedObject, on_delete=models.CASCADE, related_name='logs')
    created = models.DateTimeField(editable=False, db_index=True)

    @classmethod
    def create_moderated_object_log(cls, moderated_object_id, type, content_object):
        return cls.objects.create(log_type=type, content_object=content_object, moderated_object_id=moderated_object_id)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id and not self.created:
            self.created = timezone.now()

        return super(ModeratedObjectLog, self).save(*args, **kwargs)


class ModeratedObjectCategoryChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.ForeignKey(ModerationCategory, on_delete=models.CASCADE, related_name='+')
    changed_to = models.ForeignKey(ModerationCategory, on_delete=models.CASCADE, related_name='+')

    @classmethod
    def create_moderated_object_category_changed_log(cls, moderated_object_id, changed_from_id, changed_to_id):
        moderated_object_category_changed_log = cls.objects.create(changed_from_id=changed_from_id,
                                                                   changed_to_id=changed_to_id)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_CATEGORY_CHANGED,
                                                       content_object=moderated_object_category_changed_log,
                                                       moderated_object_id=moderated_object_id)


class ModeratedObjectDescriptionChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.CharField(_('changed from'), max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH,
                                    blank=False, null=False)
    changed_to = models.CharField(_('changed to'), max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH,
                                  blank=False, null=False)

    @classmethod
    def create_moderated_object_description_changed_log(cls, moderated_object_id, changed_from, changed_to_id):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to_id=changed_to_id)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_DESCRIPTION_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id)


class ModeratedObjectApprovedChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.BooleanField(_('changed from'),
                                       blank=False, null=False)
    changed_to = models.BooleanField(_('changed to'),
                                     blank=False, null=False)

    @classmethod
    def create_moderated_object_approved_changed_log(cls, moderated_object_id, changed_from, changed_to):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to=changed_to)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_APPROVED_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id)


class ModeratedObjectVerifiedChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.BooleanField(_('changed from'),
                                       blank=False, null=False)
    changed_to = models.BooleanField(_('changed to'),
                                     blank=False, null=False)

    @classmethod
    def create_moderated_object_verified_changed_log(cls, moderated_object_id, changed_from, changed_to):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to=changed_to)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_VERIFIED_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id)


class ModeratedObjectSubmittedChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.BooleanField(_('changed from'),
                                       blank=False, null=False)
    changed_to = models.BooleanField(_('changed to'),
                                     blank=False, null=False)

    @classmethod
    def create_moderated_object_submitted_changed_log(cls, moderated_object_id, changed_from, changed_to):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to=changed_to)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_SUBMITTED_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id)
