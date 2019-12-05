from rest_framework.fields import Field


class HashtagPostsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.show_all = kwargs.get('show_all', False)
        kwargs.pop('show_all', None)
        super(HashtagPostsCountField, self).__init__(**kwargs)

    def to_representation(self, hashtag):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous or self.show_all:
            return hashtag.count_posts()
