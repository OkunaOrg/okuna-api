from rest_framework.fields import Field

from openbook_communities.models import Community


class IsMemberField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsMemberField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.is_member_of_community_with_name(community.name)


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


class IsAdministratorField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsAdministratorField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.is_administrator_of_community_with_name(community.name)


class IsModeratorField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsModeratorField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.is_moderator_of_community_with_name(community.name)


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
