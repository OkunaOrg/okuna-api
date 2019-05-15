from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.
from django.utils import timezone

from openbook_auth.models import User
from openbook_common.utils.model_loaders import get_post_model, get_post_comment_model, get_community_model, \
    get_user_model, get_moderation_penalty_model


class ModerationCategory(models.Model):
    name = models.CharField(_('name'), max_length=32, blank=False, null=False)
    title = models.CharField(_('title'), max_length=64, blank=False, null=False)
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

    approved = models.BooleanField(_('approved'),
                                   blank=False, null=True)
    verified = models.BooleanField(_('verified'), default=False,
                                   blank=False, null=False)

    category = models.ForeignKey(ModerationCategory, on_delete=models.CASCADE, related_name='moderated_objects')

    object_audit_snapshot = models.CharField(_('object_audit_snapshot'),
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

    class Meta:
        constraints = [
            models.UniqueConstraint(name='reporter_moderated_object_constraint',
                                    fields=['object_type', 'object_id'])
        ]

    @classmethod
    def create_moderated_object(cls, object_type, object_id, category_id):
        return cls.objects.create(object_type=object_type, object_id=object_id, category_id=category_id)

    @classmethod
    def get_or_create_moderated_object(cls, object_type, object_id, category_id):
        try:
            moderated_object = cls.objects.get(object_type=object_type, object_id=object_id)
        except cls.DoesNotExist:
            moderated_object = cls.create_moderated_object(object_type=object_type,
                                                           object_id=object_id, category_id=category_id)

        return moderated_object

    def is_verified(self):
        return self.verified

    def is_approved(self):
        return self.approved is not None and self.approved

    def update_with_actor_with_id(self, actor_id, description, category_id):
        if description is not None:
            current_description = self.description
            self.description = description
            ModeratedObjectDescriptionChangedLog.create_moderated_object_description_changed_log(
                changed_from=current_description, changed_to=description, moderated_object_id=self.pk,
                actor_id=actor_id)

        if category_id is not None:
            current_category_id = self.category_id
            self.category_id = category_id
            ModeratedObjectCategoryChangedLog.create_moderated_object_category_changed_log(
                changed_from_id=current_category_id, changed_to_id=category_id, moderated_object_id=self.pk,
                actor_id=actor_id)

        self.save()

    def verify_with_actor_with_id(self, actor_id):
        current_verified = self.verified
        self.verified = True
        ModeratedObjectVerifiedChangedLog.create_moderated_object_verified_changed_log(
            changed_from=current_verified, changed_to=self.verified, moderated_object_id=self.pk, actor_id=actor_id)

        Post = get_post_model()
        PostComment = get_post_comment_model()
        Community = get_community_model()
        User = get_user_model()
        ModerationPenalty = get_moderation_penalty_model()

        content_object = self.content_object
        moderation_severity = self.category.severity
        penalty_targets = None

        if content_object is User:
            penalty_targets = [content_object]
        elif content_object is Post:
            penalty_targets = [content_object.creator]
        elif content_object is PostComment:
            penalty_targets = [content_object.commenter]
        elif content_object is Community:
            penalty_targets = content_object.get_staff_members()
        elif content_object is ModeratedObject:
            penalty_targets = content_object.get_reporters()

        for penalty_target in penalty_targets:
            duration_of_penalty = None

            if moderation_severity == ModerationCategory.SEVERITY_HIGH:
                high_severity_penalties_count = penalty_target.count_high_severity_moderation_penalties()
                duration_of_penalty = timedelta(days=high_severity_penalties_count ** 4)
            elif moderation_severity == ModerationCategory.SEVERITY_MEDIUM:
                medium_severity_penalties_count = penalty_target.count_medium_severity_moderation_penalties()
                duration_of_penalty = timedelta(hours=medium_severity_penalties_count ** 2)
            elif moderation_severity == ModerationCategory.SEVERITY_LOW:
                low_severity_penalties_count = penalty_target.count_low_severity_moderation_penalties()
                duration_of_penalty = timedelta(hours=low_severity_penalties_count ** 2)

            ModerationPenalty.create_suspension_moderation_penalty(moderated_object=self,
                                                                   user_id=penalty_target,
                                                                   duration=duration_of_penalty)

        if content_object is User:
            self.object_audit_snapshot = {
                'id': content_object.id,
                'username': content_object.username,
                'email': content_object.email,
                'name': content_object.profile.name,
                'location': content_object.profile.location,
                'bio': content_object.profile.bio,
                'url': content_object.profile.url
            }
        elif content_object is Post:
            self.object_audit_snapshot = {
                'id': content_object.id,
                'text': content_object.text,
                'creator_id': content_object.creator_id,
                'created': content_object.created,
                'community_id': content_object.community_id,
            }
        elif content_object is PostComment:
            self.object_audit_snapshot = {
                'id': content_object.id,
                'text': content_object.text,
                'commenter_id': content_object.commenter_id,
                'created': content_object.created,
                'post_id': content_object.post_id,
            }
        elif content_object is Community:
            self.object_audit_snapshot = {
                'id': content_object.id,
                'name': content_object.name,
                'title': content_object.title,
                'creator_id': content_object.creator_id,
                'staff_members_ids': ','.join([staff_member.pk for staff_member in content_object.get_staff_members()]),
                'created': content_object.created,
                'type': content_object.type,
                'description': content_object.description,
                'rules': content_object.rules,
            }
        elif content_object is ModeratedObject:
            self.object_audit_snapshot = {
                'id': content_object.id,
                'description': content_object.description,
                'category_id': content_object.category_id,
                'object_type': content_object.object_type,
                'content_type': content_object.content_type,
                'object_id': content_object.object_id,
            }

        if content_object is not User or moderation_severity == ModerationCategory.SEVERITY_CRITICAL:
            content_object.delete()

        self.save()

    def unverify_with_actor_with_id(self, actor_id):
        current_verified = self.verified
        self.verified = False
        ModeratedObjectVerifiedChangedLog.create_moderated_object_verified_changed_log(
            changed_from=current_verified, changed_to=self.verified, moderated_object_id=self.pk, actor_id=actor_id)
        self.penalties.delete()
        self.object_audit_snapshot = None
        self.save()

    def approve_with_actor_with_id(self, actor_id):
        current_approved = self.approved
        self.approved = True
        ModeratedObjectApprovedChangedLog.create_moderated_object_approved_changed_log(
            changed_from=current_approved, changed_to=self.approved, moderated_object_id=self.pk, actor_id=actor_id)
        self.save()

    def reject_with_actor_with_id(self, actor_id):
        current_approved = self.approved
        self.approved = False
        ModeratedObjectApprovedChangedLog.create_moderated_object_approved_changed_log(
            changed_from=current_approved, changed_to=self.approved, moderated_object_id=self.pk, actor_id=actor_id)
        self.save()

    def get_reporters(self):
        return User.objects.filter(moderation_reports__moderated_object_id=self.pk).all()


class ModerationReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_reports')
    moderated_object = models.ForeignKey(ModeratedObject, on_delete=models.CASCADE, related_name='reports')
    category = models.ForeignKey(ModerationCategory, on_delete=models.CASCADE, related_name='reports')
    description = models.CharField(_('description'), max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH,
                                   blank=False, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='reporter_moderated_object_constraint',
                                    fields=['reporter', 'moderated_object'])
        ]

    @classmethod
    def create_post_moderation_report(cls, reporter_id, post_id, category_id, description):
        moderated_object = ModeratedObject.get_or_create_moderated_object(object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                                          object_id=post_id,
                                                                          category_id=category_id
                                                                          )
        post_moderation_report = cls.objects.create(reporter_id=reporter_id, category_id=category_id,
                                                    description=description, moderated_object=moderated_object)
        return post_moderation_report

    @classmethod
    def create_post_comment_moderation_report(cls, reporter_id, post_comment_id, category_id, description):
        moderated_object = ModeratedObject.get_or_create_moderated_object(
            object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
            object_id=post_comment_id,
            category_id=category_id
        )
        post_comment_moderation_report = cls.objects.create(reporter_id=reporter_id,
                                                            category_id=category_id,
                                                            description=description,
                                                            moderated_object=moderated_object)
        return post_comment_moderation_report

    @classmethod
    def create_user_moderation_report(cls, reporter_id, user_id, category_id, description):
        moderated_object = ModeratedObject.get_or_create_moderated_object(object_type=ModeratedObject.OBJECT_TYPE_USER,
                                                                          object_id=user_id,
                                                                          category_id=category_id
                                                                          )
        user_moderation_report = cls.objects.create(reporter_id=reporter_id, category_id=category_id,
                                                    description=description, moderated_object=moderated_object)
        return user_moderation_report

    @classmethod
    def create_community_moderation_report(cls, reporter_id, community_id, category_id, description):
        moderated_object = ModeratedObject.get_or_create_moderated_object(
            object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY,
            object_id=community_id,
            category_id=category_id
        )
        community_moderation_report = cls.objects.create(reporter_id=reporter_id, category_id=category_id,
                                                         description=description, moderated_object=moderated_object)
        return community_moderation_report

    @classmethod
    def create_moderated_object_moderation_report(cls, reporter_id, moderated_object_id, category_id, description):
        moderated_object = ModeratedObject.get_or_create_moderated_object(
            object_type=ModeratedObject.OBJECT_TYPE_MODERATED_OBJECT,
            object_id=moderated_object_id,
            category_id=category_id
        )
        moderated_object_moderation_report = cls.objects.create(reporter_id=reporter_id, category_id=category_id,
                                                                description=description,
                                                                moderated_object=moderated_object)
        return moderated_object_moderation_report


class ModerationPenalty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_penalties')
    # If null, permanent
    duration = models.DurationField(null=True)
    moderated_object = models.ForeignKey(ModeratedObject, on_delete=models.CASCADE, related_name='penalties')

    TYPE_SUSPENSION = 'S'

    TYPES = (
        (TYPE_SUSPENSION, 'Suspension'),
    )

    type = models.CharField(max_length=5, choices=TYPES)

    @classmethod
    def create_suspension_moderation_penalty(cls, user_id, moderated_object, duration):
        return cls.objects.create(moderated_object=moderated_object, user_id=user_id, type=cls.TYPE_SUSPENSION,
                                  duration=duration)


class ModeratedObjectLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+', null=True)

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

    type = models.CharField(max_length=5, choices=LOG_TYPES)

    # Generic relation types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    moderated_object = models.ForeignKey(ModeratedObject, on_delete=models.CASCADE, related_name='logs')
    created = models.DateTimeField(editable=False, db_index=True)

    @classmethod
    def create_moderated_object_log(cls, moderated_object_id, type, content_object, actor_id):
        return cls.objects.create(log_type=type, content_object=content_object, moderated_object_id=moderated_object_id,
                                  actor_id=actor_id)

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
    def create_moderated_object_category_changed_log(cls, moderated_object_id, changed_from_id, changed_to_id,
                                                     actor_id):
        moderated_object_category_changed_log = cls.objects.create(changed_from_id=changed_from_id,
                                                                   changed_to_id=changed_to_id)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_CATEGORY_CHANGED,
                                                       content_object=moderated_object_category_changed_log,
                                                       moderated_object_id=moderated_object_id, actor_id=actor_id)


class ModeratedObjectDescriptionChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.CharField(_('changed from'), max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH,
                                    blank=False, null=False)
    changed_to = models.CharField(_('changed to'), max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH,
                                  blank=False, null=False)

    @classmethod
    def create_moderated_object_description_changed_log(cls, moderated_object_id, changed_from, changed_to, actor_id):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to=changed_to)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_DESCRIPTION_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id,
                                                       actor_id=actor_id)


class ModeratedObjectApprovedChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.BooleanField(_('changed from'),
                                       blank=False, null=False)
    changed_to = models.BooleanField(_('changed to'),
                                     blank=False, null=False)

    @classmethod
    def create_moderated_object_approved_changed_log(cls, moderated_object_id, changed_from, changed_to, actor_id):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to=changed_to)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_APPROVED_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id, actor_id=actor_id)


class ModeratedObjectVerifiedChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.BooleanField(_('changed from'),
                                       blank=False, null=False)
    changed_to = models.BooleanField(_('changed to'),
                                     blank=False, null=False)

    @classmethod
    def create_moderated_object_verified_changed_log(cls, moderated_object_id, changed_from, changed_to, actor_id):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to=changed_to)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_VERIFIED_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id, actor_id=actor_id)


class ModeratedObjectSubmittedChangedLog(models.Model):
    log = GenericRelation(ModeratedObjectLog)
    changed_from = models.BooleanField(_('changed from'),
                                       blank=False, null=False)
    changed_to = models.BooleanField(_('changed to'),
                                     blank=False, null=False)

    @classmethod
    def create_moderated_object_submitted_changed_log(cls, moderated_object_id, changed_from, changed_to, actor_id):
        moderated_object_description_changed_log = cls.objects.create(changed_from=changed_from,
                                                                      changed_to=changed_to)
        ModeratedObjectLog.create_moderated_object_log(type=ModeratedObjectLog.LOG_TYPE_SUBMITTED_CHANGED,
                                                       content_object=moderated_object_description_changed_log,
                                                       moderated_object_id=moderated_object_id, actor_id=actor_id)
