from rest_framework.fields import Field


class ParentCommentField(Field):
    def __init__(self,parent_comment_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.parent_comment_serializer = parent_comment_serializer
        super(ParentCommentField, self).__init__(**kwargs)

    def to_representation(self, post_comment_reply_notification):
        request = self.context.get('request')
        
        return self.parent_comment_serializer(post_comment_reply_notification.post_comment.parent_comment,
                                              context={"request": request},).data
