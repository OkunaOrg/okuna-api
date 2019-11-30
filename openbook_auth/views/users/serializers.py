from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_circles.models import Circle
from openbook_common.models import Badge, Emoji
from openbook_common.serializers_fields.user import FollowersCountField, FollowingCountField, PostsCountField, \
    IsFollowingField, IsConnectedField, IsFullyConnectedField, ConnectedCirclesField, FollowListsField, \
    IsPendingConnectionConfirmation, IsBlockedField, IsUserReportedField, IsFollowedField, \
    IsSubscribedToUserField
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
    posts_count = PostsCountField()
    is_following = IsFollowingField()
    is_followed = IsFollowedField()
    is_subscribed = IsSubscribedToUserField()
    is_connected = IsConnectedField()
    is_fully_connected = IsFullyConnectedField()
    connected_circles = ConnectedCirclesField(circle_serializer=GetUserUserCircleSerializer)
    follow_lists = FollowListsField(list_serializer=GetUserUserListSerializer)
    is_pending_connection_confirmation = IsPendingConnectionConfirmation()
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
            'is_subscribed',
            'is_connected',
            'is_reported',
            'is_fully_connected',
            'connected_circles',
            'follow_lists',
            'date_joined',
            'is_pending_connection_confirmation'
        )


class GetBlockedUserSerializer(serializers.ModelSerializer):
    is_blocked = IsBlockedField()
    is_following = IsFollowingField()
    is_subscribed = IsSubscribedToUserField()
    is_connected = IsConnectedField()
    is_fully_connected = IsFullyConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'is_blocked',
            'is_following',
            'is_subscribed',
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
    is_subscribed = IsSubscribedToUserField()
    is_connected = IsConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'is_following',
            'is_subscribed',
            'is_connected'
        )


class SubscribeToUserNotificationsUserSerializer(serializers.ModelSerializer):
    is_subscribed = IsSubscribedToUserField()

    class Meta:
        model = User
        fields = (
            'id',
            'is_subscribed',
        )
