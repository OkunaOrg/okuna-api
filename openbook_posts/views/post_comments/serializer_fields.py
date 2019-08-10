from rest_framework.fields import Field


class RepliesField(Field):

    DEFAULT_REPLY_COUNT = 2

    def __init__(self, post_comment_reply_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.post_comment_reply_serializer = post_comment_reply_serializer
        super(RepliesField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        sort_query = self.context.get('sort_query', '-created')
        request_user = request.user

        replies = request_user.get_comment_replies_for_comment_with_id_with_post_with_uuid(
            post_uuid=post_comment.post.uuid,
            post_comment_id=post_comment.pk
        ).order_by(sort_query)[:self.DEFAULT_REPLY_COUNT]

        return self.post_comment_reply_serializer(replies, many=True, context={"request": request}).data
