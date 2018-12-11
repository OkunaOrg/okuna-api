from rest_framework.fields import Field


class IsFollowingField(Field):
    def __init__(self, **kwargs):
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
    def __init__(self, **kwargs):
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
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowersCountField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        request_user = request.user

        if not user.profile.followers_count_visible and user.pk != request_user.pk:
            return None

        return user.count_followers()


class FollowingCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowingCountField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value.count_following()


class PostsCountField(Field):
    def __init__(self, **kwargs):
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


class ConnectedCirclesField(Field):
    def __init__(self, circle_serializer=None, **kwargs):
        assert circle_serializer is not None, (
            'A circle_serializer is required'
        )
        self.circle_serializer = circle_serializer
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(ConnectedCirclesField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        request_user = request.user

        circles = []

        if not request_user.is_anonymous:
            if not request_user.pk == user.pk and request_user.is_connected_with_user_with_id(user.pk):
                circles = request_user.get_circles_for_connection_with_user_with_id(user.pk).all()

        return self.circle_serializer(circles, context={"request": request}, many=True).data


class FollowListsField(Field):
    def __init__(self, list_serializer=None, **kwargs):
        assert list_serializer is not None, (
            'A list_serializer is required'
        )
        self.list_serializer = list_serializer
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(FollowListsField, self).__init__(**kwargs)

    def to_representation(self, user):
        request = self.context.get('request')
        request_user = request.user

        lists = []

        if not request_user.is_anonymous:
            if not request_user.pk == user.pk and request_user.is_following_user_with_id(user.pk):
                lists = request_user.get_lists_for_follow_for_user_with_id(user.pk).all()

        return self.list_serializer(lists, context={"request": request}, many=True).data
