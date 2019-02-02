from django.apps import apps


def get_circle_model():
    return apps.get_model('openbook_circles.Circle')


def get_connection_model():
    return apps.get_model('openbook_connections.Connection')


def get_follow_model():
    return apps.get_model('openbook_follows.Follow')


def get_post_model():
    return apps.get_model('openbook_posts.Post')


def get_list_model():
    return apps.get_model('openbook_lists.List')


def get_post_comment_model():
    return apps.get_model('openbook_posts.PostComment')


def get_post_reaction_model():
    return apps.get_model('openbook_posts.PostReaction')


def get_emoji_model():
    return apps.get_model('openbook_common.Emoji')


def get_emoji_group_model():
    return apps.get_model('openbook_common.EmojiGroup')


def get_user_invite_model():
    return apps.get_model('openbook_invitations.UserInvite')
