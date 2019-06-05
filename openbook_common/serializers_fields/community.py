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
