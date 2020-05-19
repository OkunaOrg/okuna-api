from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_circles.models import Circle
from openbook_common.models import Badge, Emoji
from openbook_common.serializers_fields.user import FollowersCountField, FollowingCountField, UserPostsCountField, \
    IsFollowingField, IsConnectedField, IsFullyConnectedField, ConnectedCirclesField, FollowListsField, \
    IsPendingConnectionConfirmation, IsBlockedField, IsUserReportedField, IsFollowedField, \
    AreNewPostNotificationsEnabledForUserField, IsPendingFollowRequestApproval, IsFollowRequested
from openbook_lists.models import List


class GetUserUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class GetUserUserListEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'image',
            'keyword'
        )


class GetUserUserListSerializer(serializers.ModelSerializer):
    emoji = GetUserUserListEmojiSerializer(many=False)

    class Meta:
        model = List
        fields = (
            'id',
            'name',
            'emoji'
        )


class GetUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, user_username_exists],
                                     required=True)


class GetUserUserProfileSerializer(serializers.ModelSerializer):
    badges = GetUserUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'location',
            'cover',
            'bio',
            'url',
            'badges'
        )


class GetUserUserCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
            'users_count'
        )


class GetUserUserListEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'image',
            'keyword'
        )


class GetUserUserListSerializer(serializers.ModelSerializer):
    emoji = GetUserUserListEmojiSerializer(many=False)

    class Meta:
        model = List
        fields = (
            'id',
            'name',
            'emoji'
        )


class GetUserUserSerializer(serializers.ModelSerializer):
    profile = GetUserUserProfileSerializer(many=False)
    followers_count = FollowersCountField()
    following_count = FollowingCountField()
    is_following = IsFollowingField()
    is_followed = IsFollowedField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()
    is_connected = IsConnectedField()
    is_fully_connected = IsFullyConnectedField()
    connected_circles = ConnectedCirclesField(circle_serializer=GetUserUserCircleSerializer)
    follow_lists = FollowListsField(list_serializer=GetUserUserListSerializer)
    is_pending_connection_confirmation = IsPendingConnectionConfirmation()
    is_pending_follow_request_approval = IsPendingFollowRequestApproval()
    is_follow_requested = IsFollowRequested()
    is_reported = IsUserReportedField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'followers_count',
            'following_count',
            'is_following',
            'is_followed',
            'is_follow_requested',
            'are_new_post_notifications_enabled',
            'is_connected',
            'is_reported',
            'is_fully_connected',
            'connected_circles',
            'follow_lists',
            'date_joined',
            'is_pending_connection_confirmation',
            'is_pending_follow_request_approval',
            'visibility'
        )


class LegacyGetUserUserSerializer(serializers.ModelSerializer):
    profile = GetUserUserProfileSerializer(many=False)
    followers_count = FollowersCountField()
    following_count = FollowingCountField()
    posts_count = UserPostsCountField()
    is_following = IsFollowingField()
    is_followed = IsFollowedField()
    is_follow_requested = IsFollowRequested()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()
    is_connected = IsConnectedField()
    is_fully_connected = IsFullyConnectedField()
    connected_circles = ConnectedCirclesField(circle_serializer=GetUserUserCircleSerializer)
    follow_lists = FollowListsField(list_serializer=GetUserUserListSerializer)
    is_pending_connection_confirmation = IsPendingConnectionConfirmation()
    is_pending_follow_request_approval = IsPendingFollowRequestApproval()
    is_reported = IsUserReportedField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'followers_count',
            'following_count',
            'posts_count',
            'is_following',
            'is_followed',
            'is_follow_requested',
            'are_new_post_notifications_enabled',
            'is_connected',
            'is_reported',
            'is_fully_connected',
            'connected_circles',
            'follow_lists',
            'date_joined',
            'is_pending_connection_confirmation',
            'is_pending_follow_request_approval',
            'visibility'
        )


class GetBlockedUserSerializer(serializers.ModelSerializer):
    is_blocked = IsBlockedField()
    is_following = IsFollowingField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()
    is_connected = IsConnectedField()
    is_fully_connected = IsFullyConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'is_blocked',
            'is_following',
            'are_new_post_notifications_enabled',
            'is_connected',
            'is_fully_connected'
        )


class SearchUsersSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=settings.SEARCH_QUERIES_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )


class SearchUsersUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class SearchUsersUserProfileSerializer(serializers.ModelSerializer):
    badges = SearchUsersUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name',
            'badges'
        )


class SearchUsersUserSerializer(serializers.ModelSerializer):
    profile = SearchUsersUserProfileSerializer(many=False)
    is_following = IsFollowingField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()
    is_connected = IsConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'is_following',
            'are_new_post_notifications_enabled',
            'is_connected',
            'visibility',
        )


class SubscribeToUserNewPostNotificationsUserSerializer(serializers.ModelSerializer):
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()

    class Meta:
        model = User
        fields = (
            'id',
            'are_new_post_notifications_enabled',
        )


class GetUserPostsCountUserSerializer(serializers.ModelSerializer):
    posts_count = UserPostsCountField()

    class Meta:
        model = User
        fields = (
            'id',
            'posts_count',
        )
