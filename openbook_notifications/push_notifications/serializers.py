from rest_framework import serializers

from openbook_common.utils.model_loaders import get_emoji_model, get_post_model, get_post_reaction_model, \
    get_post_comment_model, get_user_model


# TODO Circular dependency with openbook_auth.models where we call push notification senders which in turn use
# these serializers, making it impossible to reference to the User model. Redesign.

class PushNotificationsSerializers:
    def __init__(self):
        class NotificationUserSerializer(serializers.ModelSerializer):
            class Meta:
                model = get_user_model()
                fields = (
                    'id',
                    'username',
                )

        class NotificationEmojiSerializer(serializers.ModelSerializer):
            class Meta:
                model = get_emoji_model()
                fields = (
                    'id',
                    'keyword',
                )

        class NotificationPostSerializer(serializers.ModelSerializer):
            class Meta:
                model = get_post_model()
                fields = (
                    'id',
                    'uuid',
                )

        class NotificationPostReactionSerializer(serializers.ModelSerializer):
            reactor = NotificationUserSerializer()
            emoji = NotificationEmojiSerializer()
            post = NotificationPostSerializer()

            class Meta:
                model = get_post_reaction_model()
                fields = (
                    'id',
                    'reactor',
                    'emoji',
                    'post'
                )

        self.NotificationPostReactionSerializer = NotificationPostReactionSerializer

        class NotificationPostCommentSerializer(serializers.ModelSerializer):
            commenter = NotificationUserSerializer()
            post = NotificationPostSerializer()

            class Meta:
                model = get_post_comment_model()
                fields = (
                    'id',
                    'commenter',
                    'post'
                )

        self.NotificationPostCommentSerializer = NotificationPostCommentSerializer

        class FollowNotificationSerializer(serializers.Serializer):
            following_user = NotificationUserSerializer()

        self.FollowNotificationSerializer = FollowNotificationSerializer

        class ConnectionRequestNotificationSerializer(serializers.Serializer):
            connection_requester = NotificationUserSerializer()

        self.ConnectionRequestNotificationSerializer = ConnectionRequestNotificationSerializer
