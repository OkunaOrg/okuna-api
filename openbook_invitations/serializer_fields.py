from rest_framework.fields import Field


class RemainingInvitesCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(RemainingInvitesCountField, self).__init__(**kwargs)

    def to_representation(self):
        request = self.context.get('request')
        request_user = request.user

        remaining_invites_count = request_user.invites_count

        return remaining_invites_count
