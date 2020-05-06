from rest_framework.fields import Field

from openbook_common.utils.model_loaders import get_post_model
from openbook_communities.models import CommunityMembership
from openbook_posts.models import PostReaction, PostCommentReaction


class ReactionField(Field):
    def __init__(self, reaction_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.reaction_serializer = reaction_serializer
        super(ReactionField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')
        request_user = request.user

        serialized_reaction = None

        if not request_user.is_anonymous:
            try:
                reaction = request_user.get_reaction_for_post_with_id(post.pk)
                serialized_reaction = self.reaction_serializer(reaction, context={'request': request}).data
            except PostReaction.DoesNotExist:
                pass

        return serialized_reaction


class CommentsCountField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(CommentsCountField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')
        request_user = request.user

        comments_count = None

        if request_user.is_anonymous:
            comments_count = post.count_comments()
        else:
            comments_count = request_user.get_comments_count_for_post(post=post)

        return comments_count

class PostReactionsEmojiCountField(Field):
    def __init__(self, emoji_count_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.emoji_count_serializer = emoji_count_serializer
        super(PostReactionsEmojiCountField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')
        request_user = request.user

        reaction_emoji_count = []

        if request_user.is_anonymous:
            if post.public_reactions:
                Post = get_post_model()
                reaction_emoji_count = Post.get_emoji_counts_for_post_with_id(post.pk)
        else:
            reaction_emoji_count = request_user.get_emoji_counts_for_post_with_id(post.pk)

        post_reactions_serializer = self.emoji_count_serializer(reaction_emoji_count, many=True,
                                                                context={"request": request, 'post': post})

        return post_reactions_serializer.data


class CirclesField(Field):
    def __init__(self, circle_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.circle_serializer = circle_serializer
        super(CirclesField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')
        request_user = request.user
        circles = []

        if post.creator_id == request_user.pk:
            circles = post.circles

        return self.circle_serializer(circles, many=True, context={"request": request, 'post': post}).data


class PostCreatorField(Field):
    def __init__(self, community_membership_serializer, post_creator_serializer, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.community_membership_serializer = community_membership_serializer
        self.post_creator_serializer = post_creator_serializer
        super(PostCreatorField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')

        post_creator = post.creator
        post_community = post.community

        post_creator_serializer = self.post_creator_serializer(post_creator, context={"request": request}).data

        if post_community:
            try:
                post_creator_membership = post_community.memberships.get(user_id=post_creator.pk)
                post_creator_serializer['communities_memberships'] = [
                    self.community_membership_serializer(
                        post_creator_membership,
                        many=False,
                        context={
                            "request": request}).data
                ]
            except CommunityMembership.DoesNotExist:
                pass

        return post_creator_serializer


class PostIsMutedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(PostIsMutedField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')
        request_user = request.user

        is_muted = False

        if not request_user.is_anonymous:
            is_muted = request_user.has_muted_post_with_id(post_id=post.pk)

        return is_muted


class IsEncircledField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(IsEncircledField, self).__init__(**kwargs)

    def to_representation(self, post):
        request = self.context.get('request')
        request_user = request.user

        is_encircled = False

        if not request_user.is_anonymous:
            is_encircled = post.is_encircled_post()

        return is_encircled
