from django.apps import apps


def get_circle_model():
    return apps.get_model('openbook_circles.Circle')


def get_connection_model():
    return apps.get_model('openbook_connections.Connection')


def get_follow_model():
    return apps.get_model('openbook_follows.Follow')


def get_follow_request_model():
    return apps.get_model('openbook_follows.FollowRequest')


def get_post_model():
    return apps.get_model('openbook_posts.Post')


def get_top_post_model():
    return apps.get_model('openbook_posts.TopPost')


def get_trending_post_model():
    return apps.get_model('openbook_posts.TrendingPost')


def get_top_post_community_exclusion_model():
    return apps.get_model('openbook_posts.TopPostCommunityExclusion')


def get_profile_posts_community_exclusion_model():
    return apps.get_model('openbook_posts.ProfilePostsCommunityExclusion')


def get_post_media_model():
    return apps.get_model('openbook_posts.PostMedia')


def get_proxy_blacklist_domain_model():
    return apps.get_model('openbook_common.ProxyBlacklistedDomain')


def get_post_user_mention_model():
    return apps.get_model('openbook_posts.PostUserMention')


def get_post_comment_user_mention_model():
    return apps.get_model('openbook_posts.PostCommentUserMention')


def get_post_mute_model():
    return apps.get_model('openbook_posts.PostMute')


def get_post_comment_mute_model():
    return apps.get_model('openbook_posts.PostCommentMute')


def get_user_block_model():
    return apps.get_model('openbook_auth.UserBlock')


def get_list_model():
    return apps.get_model('openbook_lists.List')


def get_community_model():
    return apps.get_model('openbook_communities.Community')


def get_community_notifications_subscription_model():
    return apps.get_model('openbook_communities.CommunityNotificationsSubscription')


def get_community_invite_model():
    return apps.get_model('openbook_communities.CommunityInvite')


def get_community_log_model():
    return apps.get_model('openbook_communities.CommunityLog')


def get_post_comment_model():
    return apps.get_model('openbook_posts.PostComment')


def get_post_reaction_model():
    return apps.get_model('openbook_posts.PostReaction')


def get_post_comment_reaction_model():
    return apps.get_model('openbook_posts.PostCommentReaction')


def get_emoji_model():
    return apps.get_model('openbook_common.Emoji')


def get_emoji_group_model():
    return apps.get_model('openbook_common.EmojiGroup')


def get_user_invite_model():
    return apps.get_model('openbook_invitations.UserInvite')


def get_badge_model():
    return apps.get_model('openbook_common.Badge')


def get_language_model():
    return apps.get_model('openbook_common.Language')


def get_hashtag_model():
    return apps.get_model('openbook_hashtags.Hashtag')


def get_category_model():
    return apps.get_model('openbook_categories.Category')


def get_community_membership_model():
    return apps.get_model('openbook_communities.CommunityMembership')


def get_post_comment_notification_model():
    return apps.get_model('openbook_notifications.PostCommentNotification')


def get_post_user_mention_notification_model():
    return apps.get_model('openbook_notifications.PostUserMentionNotification')


def get_post_comment_user_mention_notification_model():
    return apps.get_model('openbook_notifications.PostCommentUserMentionNotification')


def get_post_comment_reply_notification_model():
    return apps.get_model('openbook_notifications.PostCommentReplyNotification')


def get_post_reaction_notification_model():
    return apps.get_model('openbook_notifications.PostReactionNotification')


def get_post_comment_reaction_notification_model():
    return apps.get_model('openbook_notifications.PostCommentReactionNotification')


def get_follow_notification_model():
    return apps.get_model('openbook_notifications.FollowNotification')


def get_follow_request_notification_model():
    return apps.get_model('openbook_notifications.FollowRequestNotification')


def get_follow_request_approved_notification_model():
    return apps.get_model('openbook_notifications.FollowRequestApprovedNotification')


def get_connection_request_notification_model():
    return apps.get_model('openbook_notifications.ConnectionRequestNotification')


def get_connection_confirmed_notification_model():
    return apps.get_model('openbook_notifications.ConnectionConfirmedNotification')


def get_community_invite_notification_model():
    return apps.get_model('openbook_notifications.CommunityInviteNotification')


def get_community_new_post_notification_model():
    return apps.get_model('openbook_notifications.CommunityNewPostNotification')


def get_user_new_post_notification_model():
    return apps.get_model('openbook_notifications.UserNewPostNotification')


def get_notification_model():
    return apps.get_model('openbook_notifications.Notification')


def get_device_model():
    return apps.get_model('openbook_devices.Device')


def get_user_model():
    return apps.get_model('openbook_auth.User')


def get_user_notifications_subscription_model():
    return apps.get_model('openbook_auth.UserNotificationsSubscription')


def get_moderated_object_model():
    return apps.get_model('openbook_moderation.ModeratedObject')


def get_moderation_report_model():
    return apps.get_model('openbook_moderation.ModerationReport')


def get_moderation_category_model():
    return apps.get_model('openbook_moderation.ModerationCategory')


def get_moderation_penalty_model():
    return apps.get_model('openbook_moderation.ModerationPenalty')
