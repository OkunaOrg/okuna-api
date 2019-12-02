from rest_framework.fields import Field


class CommunityPendingModeratedObjectsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(CommunityPendingModeratedObjectsCountField, self).__init__(**kwargs)

    def to_representation(self, community):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous or not request_user.is_staff_of_community_with_name(
                community_name=community.name):
            return None

        return community.count_pending_moderated_objects()

