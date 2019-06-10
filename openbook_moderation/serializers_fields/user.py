from rest_framework.fields import Field


class UserPendingCommunitiesModeratedObjectsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(UserPendingCommunitiesModeratedObjectsCountField, self).__init__(**kwargs)

    def to_representation(self, user):
        if user.is_anonymous:
            return None

        return user.count_pending_communities_moderated_objects()


class UserActiveModerationPenaltiesCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(UserActiveModerationPenaltiesCountField, self).__init__(**kwargs)

    def to_representation(self, user):
        if user.is_anonymous:
            return None

        return user.count_active_moderation_penalties()
