from rest_framework.fields import Field

from openbook_communities.models import Community


class IsInvitedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsInvitedField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.is_invited_to_community_with_name(community.name)


class AreNewPostNotificationsEnabledForCommunityField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(AreNewPostNotificationsEnabledForCommunityField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.are_new_post_notifications_enabled_for_community(community=community)


class IsCreatorField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsCreatorField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.is_creator_of_community_with_name(community.name)


class IsFavoriteField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsFavoriteField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.has_favorite_community_with_name(community.name)


class RulesField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(RulesField, self).__init__(**kwargs)

    def to_representation(self, community):
        if not community.is_private():
            return community.rules

        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous or not request_user.is_member_of_community_with_name(
                community_name=community.name):
            return None

        return community.rules


class ModeratorsField(Field):
    def __init__(self, moderator_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.moderator_serializer = moderator_serializer
        super(ModeratorsField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')

        moderators = Community.get_community_with_name_moderators(community_name=community.name)

        return self.moderator_serializer(moderators, context={"request": request}, many=True).data


class AdministratorsField(Field):
    def __init__(self, administrator_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.administrator_serializer = administrator_serializer
        super(AdministratorsField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')

        administrators = Community.get_community_with_name_administrators(community_name=community.name)

        return self.administrator_serializer(administrators, context={"request": request}, many=True).data


class CommunityMembershipsField(Field):
    def __init__(self, community_membership_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.community_membership_serializer = community_membership_serializer
        super(CommunityMembershipsField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous or not request_user.is_member_of_community_with_name(
                community_name=community.name):
            return None

        membership = community.memberships.get(user=request_user)

        return self.community_membership_serializer([membership], context={"request": request}, many=True).data


class UserCommunitiesMembershipsField(Field):
    def __init__(self, community_membership_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.community_membership_serializer = community_membership_serializer
        super(UserCommunitiesMembershipsField, self).__init__(**kwargs)

    def to_representation(self, member):
        request = self.context.get('request')
        request_user = request.user
        community = self.context.get('community')

        if not community or request_user.is_anonymous or not request_user.is_member_of_community_with_name(
                community_name=community.name):
            return None

        membership = community.memberships.get(user=request_user)

        return self.community_membership_serializer([membership], context={"request": request}, many=True).data
