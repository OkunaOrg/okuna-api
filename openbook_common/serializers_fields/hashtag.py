from rest_framework.fields import Field


class HashtagPostsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(HashtagPostsCountField, self).__init__(**kwargs)

    def to_representation(self, hashtag):
        return hashtag.count_posts()
