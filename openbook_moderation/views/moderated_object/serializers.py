from django.conf import settings
from generic_relations.relations import GenericRelatedField
from rest_framework import serializers

from openbook_auth.models import UserProfile, User
from openbook_moderation.models import ModeratedObjectLog, ModeratedObjectCategoryChangedLog, \
    ModeratedObjectDescriptionChangedLog, ModeratedObjectStatusChangedLog, ModeratedObjectVerifiedChangedLog, \
    ModerationCategory, ModerationReport
from openbook_moderation.serializers import ModeratedObjectUserProfileBadgeSerializer
from openbook_moderation.views.validators import moderated_object_id_exists, moderation_category_id_exists


class UpdateModeratedObjectSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=settings.MODERATED_OBJECT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )
    category_id = serializers.IntegerField(
        validators=[moderation_category_id_exists],
        required=False
    )


class ApproveModeratedObjectSerializer(serializers.Serializer):
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )


class RejectModeratedObjectSerializer(serializers.Serializer):
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )


class VerifyModeratedObjectSerializer(serializers.Serializer):
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )


class UnverifyModeratedObjectSerializer(serializers.Serializer):
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )


class GetModeratedObjectLogsSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    max_id = serializers.IntegerField(
        required=False,
    )
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )


class ModeratedObjectLogModerationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCategory
        fields = (
            'id',
            'name',
            'title',
            'description',
            'severity',
        )


class ModeratedObjectLogActorProfileSerializer(serializers.ModelSerializer):
    badges = ModeratedObjectUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'badges'
        )


class ModeratedObjectLogActorSerializer(serializers.ModelSerializer):
    profile = ModeratedObjectLogActorProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class ModeratedObjectCategoryChangedLogSerializer(serializers.ModelSerializer):
    changed_from = ModeratedObjectLogModerationCategorySerializer()
    changed_to = ModeratedObjectLogModerationCategorySerializer()

    class Meta:
        model = ModeratedObjectCategoryChangedLog
        fields = (
            'id',
            'changed_from',
            'changed_to'
        )


class ModeratedObjectDescriptionChangedLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeratedObjectDescriptionChangedLog
        fields = (
            'id',
            'changed_from',
            'changed_to'
        )


class ModeratedObjectStatusChangedLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeratedObjectStatusChangedLog
        fields = (
            'id',
            'changed_from',
            'changed_to'
        )


class ModeratedObjectVerifiedChangedLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeratedObjectVerifiedChangedLog
        fields = (
            'id',
            'changed_from',
            'changed_to'
        )


class ModeratedObjectLogSerializer(serializers.ModelSerializer):
    actor = ModeratedObjectLogActorSerializer()

    content_object = GenericRelatedField({
        ModeratedObjectCategoryChangedLog: ModeratedObjectCategoryChangedLogSerializer(),
        ModeratedObjectDescriptionChangedLog: ModeratedObjectDescriptionChangedLogSerializer(),
        ModeratedObjectStatusChangedLog: ModeratedObjectStatusChangedLogSerializer(),
        ModeratedObjectVerifiedChangedLog: ModeratedObjectVerifiedChangedLogSerializer(),
    })

    class Meta:
        model = ModeratedObjectLog
        fields = (
            'id',
            'log_type',
            'actor',
            'content_object',
            'created'
        )


class ModeratedObjectReportReporterProfileSerializer(serializers.ModelSerializer):
    badges = ModeratedObjectUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name',
            'badges'
        )


class ModeratedObjectReportReporterSerializer(serializers.ModelSerializer):
    profile = ModeratedObjectReportReporterProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class GetModeratedObjectReportsSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    max_id = serializers.IntegerField(
        required=False,
    )
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )


class ModeratedObjectReportModerationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCategory
        fields = (
            'id',
            'name',
            'title',
            'description',
            'severity',
        )


class ModeratedObjectReportSerializer(serializers.ModelSerializer):
    category = ModeratedObjectReportModerationCategorySerializer()
    reporter = ModeratedObjectReportReporterSerializer()

    class Meta:
        model = ModerationReport
        fields = (
            'id',
            'category',
            'description',
            'reporter',
        )
