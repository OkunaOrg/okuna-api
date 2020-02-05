from rest_framework.fields import Field


class IsCommunityReportedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsCommunityReportedField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.has_reported_community_with_id(value.pk)

        return False


class CommunityPostsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(CommunityPostsCountField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return None

        if community.is_community_with_name_private(community_name=community.name) and \
                not request_user.is_member_of_community_with_name(community_name=community.name):
            return None

        return request_user.count_posts_for_community(community)
