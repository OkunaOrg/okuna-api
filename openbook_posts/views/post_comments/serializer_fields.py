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


class RepliesField(Field):
    SORT_CHOICE_TO_QUERY = {
        'DESC': '-created',
        'ASC': 'created'
    }
    DEFAULT_REPLY_COUNT = 2

    def __init__(self, post_comment_reply_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.post_comment_reply_serializer = post_comment_reply_serializer
        super(RepliesField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        request_user = request.user
        request_data = request.query_params.dict()
        sort = request_data.get('sort', 'DESC')
        sort_query = self.SORT_CHOICE_TO_QUERY[sort]

        replies = request_user.get_comment_replies_for_post_with_id_for_comment_with_id(
            post_id=post_comment.post.pk,
            post_comment_id=post_comment.pk
        ).order_by(sort_query)[:self.DEFAULT_REPLY_COUNT]

        return self.post_comment_reply_serializer(replies, many=True, context={"request": request}).data
