from generic_relations.relations import GenericRelatedField
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Emoji
from openbook_communities.models import Community, CommunityInvite
from openbook_notifications.models import Notification, PostCommentNotification, ConnectionRequestNotification, \
    ConnectionConfirmedNotification, FollowNotification, CommunityInviteNotification
from openbook_notifications.models.post_reaction_notification import PostReactionNotification
from openbook_notifications.validators import notification_id_exists
from openbook_posts.models import PostComment, PostReaction, Post, PostImage, PostVideo


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


class PostCommentPostVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVideo
        fields = (
            'id',
            'video',
        )


class PostCommentPostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = (
            'id',
            'image',
            'width',
            'height'
        )


class NotificationPostSerializer(serializers.ModelSerializer):
    image = PostCommentPostImageSerializer()
    video = PostCommentPostVideoSerializer()

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'image',
            'text',
            'video',
        )


class PostCommentSerializer(serializers.ModelSerializer):
    commenter = PostCommentCommenterSerializer()
    post = NotificationPostSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'commenter',
            'text',
            'post'
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


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image'
        )


class PostReactionSerializer(serializers.ModelSerializer):
    reactor = PostReactionReactorSerializer()
    emoji = PostReactionEmojiSerializer()
    post = NotificationPostSerializer()

    class Meta:
        model = PostReaction
        fields = (
            'id',
            'reactor',
            'emoji',
            'post'
        )


class PostReactionNotificationSerializer(serializers.ModelSerializer):
    post_reaction = PostReactionSerializer()

    class Meta:
        model = PostReactionNotification
        fields = (
            'id',
            'post_reaction'
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


class FollowerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar'
        )


class FollowerSerializer(serializers.ModelSerializer):
    profile = FollowerProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class FollowNotificationSerializer(serializers.ModelSerializer):
    follower = FollowerSerializer()

    class Meta:
        model = FollowNotification
        fields = (
            'id',
            'follower'
        )


class CommunityInviteCreatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar'
        )


class CommunityInviteCreatorSerializer(serializers.ModelSerializer):
    profile = CommunityInviteCreatorProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class CommunityInviteCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'avatar',
            'cover',
            'color'
        )


class CommunityInviteSerializer(serializers.ModelSerializer):
    creator = CommunityInviteCreatorSerializer()
    community = CommunityInviteCommunitySerializer()

    class Meta:
        model = CommunityInvite
        fields = (
            'id',
            'creator',
            'invited_user_id',
            'community'
        )


class CommunityInviteNotificationSerializer(serializers.ModelSerializer):
    community_invite = CommunityInviteSerializer()

    class Meta:
        model = CommunityInviteNotification
        fields = (
            'id',
            'community_invite'
        )


class GetNotificationsNotificationSerializer(serializers.ModelSerializer):
    content_object = GenericRelatedField({
        PostCommentNotification: PostCommentNotificationSerializer(),
        PostReactionNotification: PostReactionNotificationSerializer(),
        ConnectionRequestNotification: ConnectionRequestNotificationSerializer(),
        ConnectionConfirmedNotification: ConnectionConfirmedNotificationSerializer(),
        FollowNotification: FollowNotificationSerializer(),
        CommunityInviteNotification: CommunityInviteNotificationSerializer()
    })

    class Meta:
        model = Notification
        fields = (
            'id',
            'notification_type',
            'content_object',
            'read',
            'created',
        )


class DeleteNotificationSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField(required=True,
                                               validators=[notification_id_exists])


class ReadNotificationSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField(required=True,
                                               validators=[notification_id_exists])
