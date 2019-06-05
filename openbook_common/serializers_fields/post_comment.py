from rest_framework.fields import Field


class PostCommenterField(Field):
    def __init__(self, community_membership_serializer, post_commenter_serializer, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.community_membership_serializer = community_membership_serializer
        self.post_commenter_serializer = post_commenter_serializer
        super(PostCommenterField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        post = post_comment.post
        post_commenter = post_comment.commenter
        post_community = post.community

        post_commenter_serializer = self.post_commenter_serializer(post_commenter, context={"request": request}).data

        if post_community:
            post_creator_memberships = post_community.memberships.filter(user=post_commenter).all()
            post_commenter_serializer['communities_memberships'] = self.community_membership_serializer(
                post_creator_memberships,
                many=True,
                context={
                    "request": request}).data

        return post_commenter_serializer


class RepliesCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(RepliesCountField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            replies_count = post_comment.count_replies()
        else:
            replies_count = request_user.get_replies_count_for_post_comment(post_comment=post_comment)

        return replies_count
