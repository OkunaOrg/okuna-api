from rest_framework.fields import Field


class RepliesCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(RepliesCountField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        request_user = request.user

        replies_count = request_user.get_replies_count_for_post_comment(post_comment=post_comment)

        return replies_count
