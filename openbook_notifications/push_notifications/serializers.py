from rest_framework import serializers

from openbook_common.utils.model_loaders import get_emoji_model, get_post_model, get_post_reaction_model, \
    get_post_comment_model, get_user_model, get_notification_model, get_community_invite_model, get_community_model


# TODO Circular dependency with openbook_auth.models where we call push notification senders which in turn use
# these serializers, making it impossible to reference to the User model. Redesign. Perhaps make these push
# notifications, part of a job to be sent async.

class PushNotificationsSerializers:
    def __init__(self):
        PostReaction = get_post_reaction_model()
        PostComment = get_post_comment_model()
        User = get_user_model()
        Emoji = get_emoji_model()
        Post = get_post_model()
        CommunityInvite = get_community_invite_model()
        Community = get_community_model()

        class NotificationUserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = (
                    'id',
                    'username',
                )

        class NotificationEmojiSerializer(serializers.ModelSerializer):
            class Meta:
                model = Emoji
                fields = (
                    'id',
                    'keyword',
                )

        class NotificationPostSerializer(serializers.ModelSerializer):
            class Meta:
                model = Post
                fields = (
                    'id',
                    'uuid',
                )

        class NotificationPostReactionSerializer(serializers.ModelSerializer):
            reactor = NotificationUserSerializer()
            emoji = NotificationEmojiSerializer()
            post = NotificationPostSerializer()

            class Meta:
                model = PostReaction
                fields = (
                    'id',
                    'reactor',
                    'emoji',
                    'post'
                )

        self.NotificationPostReactionSerializer = NotificationPostReactionSerializer

        class NotificationCommunitySerializer(serializers.ModelSerializer):
            class Meta:
                model = Community
                fields = (
                    'id',
                    'name',
                    'title'
                )

        class NotificationCommunityInviteSerializer(serializers.ModelSerializer):
            creator = NotificationUserSerializer()
            invited_user = NotificationUserSerializer()
            community = NotificationCommunitySerializer()

            class Meta:
                model = CommunityInvite
                fields = (
                    'id',
                    'creator',
                    'invited_user',
                    'community'
                )

        self.NotificationCommunityInviteSerializer = NotificationCommunityInviteSerializer

        class NotificationPostCommentSerializer(serializers.ModelSerializer):
            commenter = NotificationUserSerializer()
            post = NotificationPostSerializer()

            class Meta:
                model = PostComment
                fields = (
                    'id',
                    'commenter',
                    'post'
                )

        self.NotificationPostCommentSerializer = NotificationPostCommentSerializer

        class NotificationPostCommentReplySerializer(serializers.ModelSerializer):
            commenter = NotificationUserSerializer()
            post = NotificationPostSerializer()

            class Meta:
                model = PostComment
                fields = (
                    'id',
                    'commenter',
                    'post'
                )

        self.NotificationPostCommentReplySerializer = NotificationPostCommentReplySerializer

        class FollowNotificationSerializer(serializers.Serializer):
            following_user = NotificationUserSerializer()

        self.FollowNotificationSerializer = FollowNotificationSerializer

        class ConnectionRequestNotificationSerializer(serializers.Serializer):
            connection_requester = NotificationUserSerializer()

        self.ConnectionRequestNotificationSerializer = ConnectionRequestNotificationSerializer
