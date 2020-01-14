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

        return request_user.count_posts_for_hashtag(hashtag=hashtag)


class IsHashtagReportedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsHashtagReportedField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.has_reported_hashtag_with_id(value.pk)

        return False
