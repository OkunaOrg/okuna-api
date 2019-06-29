from rest_framework.fields import Field

from openbook_common.utils.model_loaders import get_post_comment_model
from openbook_posts.models import PostCommentReaction


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


class PostCommentReactionsEmojiCountField(Field):
    def __init__(self, emoji_count_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.emoji_count_serializer = emoji_count_serializer
        super(PostCommentReactionsEmojiCountField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        request_user = request.user

        if request_user.is_anonymous:
            PostComment = get_post_comment_model()
            reaction_emoji_count = PostComment.get_emoji_counts_for_post_comment_with_id(post_comment.pk)
        else:
            reaction_emoji_count = request_user.get_emoji_counts_for_post_comment(post_comment=post_comment)

        post_comment_reactions_serializer = self.emoji_count_serializer(reaction_emoji_count, many=True,
                                                                        context={"request": request,
                                                                                 'post_comment': post_comment})

        return post_comment_reactions_serializer.data


class PostCommentReactionField(Field):
    def __init__(self, post_comment_reaction_serializer=None, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        self.comment_reaction_serializer = post_comment_reaction_serializer
        super(PostCommentReactionField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        request_user = request.user

        serialized_commentReaction = None

        if not request_user.is_anonymous:
            try:
                comment_reaction = request_user.get_reaction_for_post_comment_with_id(post_comment.pk)
                serialized_commentReaction = self.comment_reaction_serializer(comment_reaction,
                                                                              context={'request': request}).data
            except PostCommentReaction.DoesNotExist:
                pass

        return serialized_commentReaction


class PostCommentIsMutedField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(PostCommentIsMutedField, self).__init__(**kwargs)

    def to_representation(self, post_comment):
        request = self.context.get('request')
        request_user = request.user

        is_muted = False

        if not request_user.is_anonymous:
            is_muted = request_user.has_muted_post_comment_with_id(post_comment_id=post_comment.pk)

        return is_muted
