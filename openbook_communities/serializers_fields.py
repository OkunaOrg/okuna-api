from rest_framework.fields import Field


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

class IsAdminField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsAdminField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.is_administrator_of_community_with_name(community.name)


class IsModField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsModField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.is_moderator_of_community_with_name(community.name)