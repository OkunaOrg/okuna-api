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


def get_community_model():
    return apps.get_model('openbook_communities.Community')


def get_community_invite_model():
    return apps.get_model('openbook_communities.CommunityInvite')


def get_community_log_model():
    return apps.get_model('openbook_communities.CommunityLog')


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


def get_badge_model():
    return apps.get_model('openbook_common.Badge')


def get_tag_model():
    return apps.get_model('openbook_tags.Tag')


def get_category_model():
    return apps.get_model('openbook_categories.Category')


def get_community_membership_model():
    return apps.get_model('openbook_communities.CommunityMembership')


def get_post_comment_notification_model():
    return apps.get_model('openbook_notifications.PostCommentNotification')


def get_post_reaction_notification_model():
    return apps.get_model('openbook_notifications.PostReactionNotification')


def get_follow_notification_model():
    return apps.get_model('openbook_notifications.FollowNotification')


def get_connection_request_notification_model():
    return apps.get_model('openbook_notifications.ConnectionRequestNotification')


def get_connection_confirmed_notification_model():
    return apps.get_model('openbook_notifications.ConnectionConfirmedNotification')


def get_notification_model():
    return apps.get_model('openbook_notifications.Notification')


def get_device_model():
    return apps.get_model('openbook_devices.Device')


def get_user_model():
    return apps.get_model('openbook_auth.User')
