from rest_framework.fields import Field

from openbook_communities.models import CommunityInvite
from openbook_common.utils.model_loaders import get_user_model


class IsFollowingField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsFollowingField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.is_following_user_with_id(value.pk)

        return False


class AreNewPostNotificationsEnabledForUserField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(AreNewPostNotificationsEnabledForUserField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.are_new_post_notifications_enabled_for_user(user=value)

        return False


class IsFollowedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsFollowedField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == user.pk:
                return False
            return user.is_following_user_with_id(request.user.pk)

        return False


class IsUserReportedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsUserReportedField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            reported = request.user.has_reported_user_with_id(value.pk)
            return reported

        return False


class IsMemberOfCommunities(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsMemberOfCommunities, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        request_user = request.user

        return request_user.is_member_of_communities()


class IsConnectedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsConnectedField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.is_connected_with_user_with_id(value.pk)

        return False


class IsBlockedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsBlockedField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.has_blocked_user_with_id(value.pk)

        return False


class IsFullyConnectedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsFullyConnectedField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.is_fully_connected_with_user_with_id(value.pk)

        return False


class IsPendingConnectionConfirmation(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsPendingConnectionConfirmation, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.is_pending_confirm_connection_for_user_with_id(value.pk)

        return False


class IsPendingFollowRequestApproval(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsPendingFollowRequestApproval, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.has_follow_request_from_user_with_id(value.pk)

        return False


class IsFollowRequested(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsFollowRequested, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return value.has_follow_request_from_user_with_id(request.user.pk)

        return False


class FollowersCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowersCountField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        request_user = request.user

        if not user.profile.followers_count_visible and user.pk != request_user.pk:
            return None

        return user.count_followers()


class IsGlobalModeratorField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsGlobalModeratorField, self).__init__(**kwargs)

    def to_representation(self, user):
        return user.is_global_moderator()


class FollowingCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowingCountField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value.count_following()


class UserPostsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(UserPostsCountField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return value.count_posts()
            return value.count_posts_for_user_with_id(request.user.pk)

        User = get_user_model()
        return User.count_unauthenticated_public_posts_for_user_with_username(username=value.username)


class UnreadNotificationsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(UnreadNotificationsCountField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')
        request_user = request.user

        if not request_user.is_anonymous:
            return request_user.count_unread_notifications()

        return None


class ConnectedCirclesField(Field):
    def __init__(self, circle_serializer=None, **kwargs):
        self.circle_serializer = circle_serializer
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(ConnectedCirclesField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        request_user = request.user

        circles = []

        if not request_user.is_anonymous:
            if not request_user.pk == user.pk and request_user.is_connected_with_user_with_id(user.pk):
                circles = request_user.get_circles_for_connection_with_user_with_id(user.pk).all()

        return self.circle_serializer(circles, context={"request": request}, many=True).data


class FollowListsField(Field):
    def __init__(self, list_serializer=None, **kwargs):
        self.list_serializer = list_serializer
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowListsField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        request_user = request.user

        lists = []

        if not request_user.is_anonymous:
            if not request_user.pk == user.pk and request_user.is_following_user_with_id(user.pk):
                lists = request_user.get_lists_for_follow_for_user_with_id(user.pk).all()

        return self.list_serializer(lists, context={"request": request}, many=True).data


class CommunitiesMembershipsField(Field):
    def __init__(self, community_membership_serializer, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.community_membership_serializer = community_membership_serializer
        super(CommunitiesMembershipsField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        communities_names = self.context.get('communities_names')

        request_user = request.user

        memberships = []

        for community_name in communities_names:
            if not community_name:
                continue

            if not request_user.is_member_of_community_with_name(community_name=community_name):
                continue

            if not user.is_member_of_community_with_name(community_name=community_name):
                continue

            community_membership = user.communities_memberships.get(community__name=community_name)

            memberships.append(community_membership)

        if not memberships:
            return None

        return self.community_membership_serializer(memberships, context={"request": request}, many=True).data


class CommunitiesInvitesField(Field):
    # Retrieve the invites for the given communities_names of the request user to
    # the serialized user
    def __init__(self, community_invite_serializer, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.community_invite_serializer = community_invite_serializer
        super(CommunitiesInvitesField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        communities_names = self.context.get('communities_names')

        request_user = request.user

        community_invites = []

        for community_name in communities_names:
            if not community_name:
                continue

            try:
                community_invite = CommunityInvite.objects.get(creator=request_user, invited_user=user,
                                                               community__name=community_name)
                community_invites.append(community_invite)
            except CommunityInvite.DoesNotExist:
                pass

        if not community_invites:
            return None

        return self.community_invite_serializer(community_invites, context={"request": request}, many=True).data
