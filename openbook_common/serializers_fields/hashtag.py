from rest_framework.fields import Field


class HashtagPostsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(HashtagPostsCountField, self).__init__(**kwargs)

    def to_representation(self, hashtag):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            return hashtag.count_posts()

        return request_user.count_posts_for_hashtag(hashtag=hashtag)
