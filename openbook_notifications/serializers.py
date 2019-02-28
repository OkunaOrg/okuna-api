from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_notifications.models import Notification, PostCommentNotification, ConnectionRequestNotification, \
    ConnectionConfirmedNotification
from openbook_notifications.models.post_reaction_notification import PostReactionNotification
from openbook_notifications.validators import notification_id_exists
from openbook_posts.models import PostComment, PostReaction


class GetNotificationsSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    max_id = serializers.IntegerField(
        required=False,
    )


class PostCommentCommenterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar'
        )


class PostCommentCommenterSerializer(serializers.ModelSerializer):
    profile = PostCommentCommenterProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class PostCommentSerializer(serializers.ModelSerializer):
    commenter = PostCommentCommenterSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'commenter'
        )


class PostCommentNotificationSerializer(serializers.ModelSerializer):
    post_comment = PostCommentSerializer()

    class Meta:
        model = PostCommentNotification
        fields = (
            'id',
            'post_comment'
        )


class PostReactionReactorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar'
        )


class PostReactionReactorSerializer(serializers.ModelSerializer):
    profile = PostReactionReactorProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class PostReactionSerializer(serializers.ModelSerializer):
    reactor = PostReactionReactorSerializer()

    class Meta:
        model = PostReaction
        fields = (
            'id',
            'reactor'
        )


class PostReactionNotificationSerializer(serializers.ModelSerializer):
    post_comment = PostReactionSerializer()

    class Meta:
        model = PostReactionNotification
        fields = (
            'id',
            'post_comment'
        )


class ConnectionRequesterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar'
        )


class ConnectionRequesterSerializer(serializers.ModelSerializer):
    profile = ConnectionRequesterProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class ConnectionRequestNotificationSerializer(serializers.ModelSerializer):
    connection_requester = ConnectionRequesterSerializer()

    class Meta:
        model = ConnectionRequestNotification
        fields = (
            'id',
            'connection_requester'
        )


class ConnectionConfirmatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar'
        )


class ConnectionConfirmatorSerializer(serializers.ModelSerializer):
    profile = ConnectionConfirmatorProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class ConnectionConfirmedNotificationSerializer(serializers.ModelSerializer):
    connection_confirmator = ConnectionConfirmatorSerializer()

    class Meta:
        model = ConnectionConfirmedNotification
        fields = (
            'id',
            'connection_confirmator'
        )


class GetNotificationsNotificationContentObjectSerializer(serializers.RelatedField):
    def to_representation(self, value):
        if isinstance(value, PostCommentNotification):
            serializer = PostCommentNotificationSerializer(value)
        elif isinstance(value, PostReactionNotification):
            serializer = PostReactionNotificationSerializer(value)
        elif isinstance(value, ConnectionRequestNotification):
            serializer = ConnectionRequestNotificationSerializer(value)
        elif isinstance(value, ConnectionRequestNotification):
            serializer = ConnectionRequestNotificationSerializer(value)
        elif isinstance(value, ConnectionConfirmedNotification):
            serializer = ConnectionConfirmedNotificationSerializer(value)
        else:
            raise Exception('Unexpected type notification content object')

        return serializer.data


class GetNotificationsNotificationSerializer(serializers.ModelSerializer):
    content_object = GetNotificationsNotificationContentObjectSerializer()

    class Meta:
        model = Notification
        fields = (
            'id',
            'notification_type',
            'content_object'
        )


class DeleteNotificationSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField(allow_blank=False,
                                               required=True,
                                               validators=[notification_id_exists])

class ReadNotificationSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField(allow_blank=False,
                                               required=True,
                                               validators=[notification_id_exists])
