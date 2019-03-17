from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext as _

from openbook.settings import USERNAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH, PROFILE_NAME_MAX_LENGTH
from openbook_auth.models import User, UserProfile, UserNotificationsSettings
from openbook_auth.validators import username_characters_validator, \
    username_not_taken_validator, email_not_taken_validator, user_username_exists, \
    is_of_legal_age_validator, user_email_exists
from django.contrib.auth.password_validation import validate_password

from openbook_circles.models import Circle
from openbook_common.models import Emoji, Badge
from openbook_common.serializers_fields.request import FriendlyUrlField, RestrictedImageFileSizeField
from openbook_common.serializers_fields.user import IsFollowingField, IsConnectedField, FollowersCountField, \
    FollowingCountField, PostsCountField, ConnectedCirclesField, FollowListsField, IsFullyConnectedField, \
    IsPendingConnectionConfirmation, CommunitiesMembershipsField, CommunitiesInvitesField, IsMemberOfCommunities, \
    UnreadNotificationsCountField
from openbook_common.validators import name_characters_validator
from openbook_communities.models import CommunityMembership, CommunityInvite
from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_lists.models import List


class RegisterSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password])
    is_of_legal_age = serializers.BooleanField(validators=[is_of_legal_age_validator])
    name = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH,
                                 allow_blank=False, validators=[name_characters_validator])
    avatar = RestrictedImageFileSizeField(allow_empty_file=True, required=False,
                                          max_upload_size=settings.PROFILE_AVATAR_MAX_SIZE)
    email = serializers.EmailField(validators=[email_not_taken_validator])
    token = serializers.CharField()


class UsernameCheckSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, username_not_taken_validator])


class EmailCheckSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_not_taken_validator])


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator])
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class GetAuthenticatedUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    badges = BadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'name',
            'avatar',
            'bio',
            'url',
            'location',
            'cover',
            'is_of_legal_age',
            'followers_count_visible',
            'badges'
        )


class GetAuthenticatedUserSerializer(serializers.ModelSerializer):
    profile = GetAuthenticatedUserProfileSerializer(many=False)
    posts_count = PostsCountField()
    unread_notifications_count = UnreadNotificationsCountField()
    followers_count = FollowersCountField()
    following_count = FollowingCountField()
    is_member_of_communities = IsMemberOfCommunities()

    class Meta:
        model = User
        fields = (
            'id',
            'uuid',
            'email',
            'username',
            'profile',
            'posts_count',
            'followers_count',
            'following_count',
            'connections_circle_id',
            'is_member_of_communities',
            'unread_notifications_count'
        )


class UpdateAuthenticatedUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator],
                                     required=False)
    avatar = RestrictedImageFileSizeField(allow_empty_file=False, required=False, allow_null=True,
                                          max_upload_size=settings.PROFILE_AVATAR_MAX_SIZE)
    cover = RestrictedImageFileSizeField(allow_empty_file=False, required=False, allow_null=True,
                                         max_upload_size=settings.PROFILE_COVER_MAX_SIZE)
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password], required=False, allow_blank=False)
    name = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH,
                                 required=False,
                                 allow_blank=False, validators=[name_characters_validator])
    followers_count_visible = serializers.BooleanField(required=False, default=None, allow_null=True)
    bio = serializers.CharField(max_length=settings.PROFILE_BIO_MAX_LENGTH, required=False,
                                allow_blank=True)
    url = FriendlyUrlField(required=False,
                           allow_blank=True)
    location = serializers.CharField(max_length=settings.PROFILE_LOCATION_MAX_LENGTH, required=False,
                                     allow_blank=True)


class DeleteAuthenticatedUserSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password], required=True, allow_blank=False)


class UpdateUserSettingsSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                         validators=[validate_password], required=False, allow_blank=False)
    current_password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                             validators=[validate_password], required=False, allow_blank=False)
    email = serializers.EmailField(validators=[email_not_taken_validator], required=False)

    def validate(self, data):
        if 'new_password' not in data and 'current_password' in data:
            raise serializers.ValidationError(_('New password must be supplied together with the current password'))

        if 'new_password' in data and 'current_password' not in data:
            raise serializers.ValidationError(_('Current password must be supplied together with the new password'))

        return data


class GetUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, user_username_exists],
                                     required=True)


class GetUserUserProfileSerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True)

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
    is_connected = IsConnectedField()
    is_fully_connected = IsFullyConnectedField()
    connected_circles = ConnectedCirclesField(circle_serializer=GetUserUserCircleSerializer)
    follow_lists = FollowListsField(list_serializer=GetUserUserListSerializer)
    is_pending_connection_confirmation = IsPendingConnectionConfirmation()

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
            'is_connected',
            'is_fully_connected',
            'connected_circles',
            'follow_lists',
            'is_pending_connection_confirmation'
        )


class GetUsersSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=settings.SEARCH_QUERIES_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )


class GetLinkedUsersSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )
    with_community = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class SearchLinkedUsersSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=settings.SEARCH_QUERIES_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )
    with_community = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class GetUsersUserProfileSerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name',
            'badges'
        )


class GetUsersUserSerializer(serializers.ModelSerializer):
    profile = GetUsersUserProfileSerializer(many=False)
    is_following = IsFollowingField()
    is_connected = IsConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'is_following',
            'is_connected'
        )


class GetLinkedUsersUserCommunityMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = (
            'id',
            'user_id',
            'community_id',
            'is_administrator',
            'is_moderator',
        )


class GetLinkedUsersUserCommunityInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityInvite
        fields = (
            'id',
            'creator_id',
            'invited_user_id',
            'community_id'
        )


class GetLinkedUsersUserSerializer(serializers.ModelSerializer):
    profile = GetUsersUserProfileSerializer(many=False)
    communities_memberships = CommunitiesMembershipsField(
        community_membership_serializer=GetLinkedUsersUserCommunityMembershipSerializer)
    communities_invites = CommunitiesInvitesField(
        community_invite_serializer=GetLinkedUsersUserCommunityInviteSerializer
    )

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'communities_memberships',
            'communities_invites'
        )


class AuthenticatedUserNotificationsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationsSettings
        fields = (
            'id',
            'post_comment_notifications',
            'post_reaction_notifications',
            'follow_notifications',
            'connection_request_notifications',
            'connection_confirmed_notifications',
            'community_invite_notifications',
        )


class UpdateAuthenticatedUserNotificationsSettingsSerializer(serializers.Serializer):
    post_comment_notifications = serializers.BooleanField(required=False)
    post_reaction_notifications = serializers.BooleanField(required=False)
    follow_notifications = serializers.BooleanField(required=False)
    connection_request_notifications = serializers.BooleanField(required=False)
    connection_confirmed_notifications = serializers.BooleanField(required=False)
    community_invite_notifications = serializers.BooleanField(required=False)


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, validators=[user_email_exists])
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH, required=False, validators=[user_username_exists])
