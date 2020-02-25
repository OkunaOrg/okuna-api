from rest_framework.fields import Field


class PostNotificationsEnabledField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(PostNotificationsEnabledField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return False

        return request_user.are_post_notifications_enabled_for_post(post=post)
