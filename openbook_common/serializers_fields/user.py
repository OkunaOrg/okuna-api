from rest_framework.fields import Field


class IsFollowingField(Field):
    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsFollowingField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.is_following_user_with_id(value.pk)

        return False


class IsConnectedField(Field):
    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsConnectedField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return False
            return request.user.is_connected_with_user_with_id(value.pk)

        return False


class FollowersCountField(Field):
    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowersCountField, self).__init__(**kwargs)

    def to_representation(self, value):
        if value.profile.followers_count_visible:
            return value.count_followers()
        return None


class FollowingCountField(Field):
    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowingCountField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value.count_following()


class PostsCountField(Field):
    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(PostsCountField, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == value.pk:
                return value.count_posts()
            return value.count_posts_for_user_with_id(request.user.pk)

        return value.count_public_posts()
