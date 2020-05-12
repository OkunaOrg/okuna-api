import django_rq
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
import onesignal as onesignal_sdk

from openbook_common.utils.model_loaders import get_notification_model
from openbook_notifications.django_rq_jobs import send_notification_to_user_with_id
from openbook_translation import translation_strategy

import logging

logger = logging.getLogger(__name__)

NOTIFICATION_GROUP_LOW_PRIORITY = 'low'
NOTIFICATION_GROUP_MEDIUM_PRIORITY = 'medium'
NOTIFICATION_GROUP_HIGH_PRIORITY = 'high'


def send_post_reaction_push_notification(post_reaction):
    post_creator = post_reaction.post.creator

    notification_group = NOTIFICATION_GROUP_LOW_PRIORITY

    if post_creator.has_reaction_notifications_enabled_for_post_with_id(post_id=post_reaction.post_id):
        post_reactor = post_reaction.reactor
        target_user_language_code = get_notification_language_code_for_target_user(post_creator)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(post_body={
                "contents": {"en": _('%(post_reactor_name)s · @%(post_reactor_username)s reacted to your post.') % {
                    'post_reactor_username': post_reactor.username,
                    'post_reactor_name': post_reactor.profile.name,

                }}
            })

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.POST_REACTION,
        }

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(notification=one_signal_notification, user=post_creator)


def send_post_comment_push_notification_with_message(post_comment, message, target_user):
    Notification = get_notification_model()

    notification_group = NOTIFICATION_GROUP_LOW_PRIORITY

    one_signal_notification = onesignal_sdk.Notification(post_body={
        "contents": message
    })

    notification_data = {
        'type': Notification.POST_COMMENT,
    }

    one_signal_notification.set_parameter('data', notification_data)
    one_signal_notification.set_parameter('!thread_id', notification_group)
    one_signal_notification.set_parameter('android_group', notification_group)

    _send_notification_to_user(notification=one_signal_notification, user=target_user)


def send_follow_push_notification(followed_user, following_user):
    if followed_user.has_follow_notifications_enabled():
        target_user_language_code = get_notification_language_code_for_target_user(followed_user)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(post_body={
                "contents": {"en": _('%(following_user_name)s · @%(following_user_username)s started following you') % {
                    'following_user_name': following_user.profile.name,
                    'following_user_username': following_user.username,
                }}
            })

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.FOLLOW,
        }

        notification_group = NOTIFICATION_GROUP_MEDIUM_PRIORITY

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(notification=one_signal_notification, user=followed_user)


def send_follow_request_push_notification(follow_request):
    follow_requester = follow_request.creator
    follow_request_target_user = follow_request.target_user

    if follow_request_target_user.has_follow_request_notifications_enabled():
        target_user_language_code = get_notification_language_code_for_target_user(follow_request_target_user)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(
                post_body={"contents": {"en": _(
                    '%(follow_requester_name)s · @%(follow_requester_username)s wants to follow you.') % {
                                                  'follow_requester_username': follow_requester.username,
                                                  'follow_requester_name': follow_requester.profile.name,
                                              }}})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.FOLLOW_REQUEST,
        }

        notification_group = NOTIFICATION_GROUP_MEDIUM_PRIORITY

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(user=follow_request_target_user, notification=one_signal_notification)


def send_follow_request_approved_push_notification(follow):
    follow_requester = follow.user
    followed_user = follow.followed_user

    if follow_requester.has_follow_request_approved_notifications_enabled():
        target_user_language_code = get_notification_language_code_for_target_user(follow_requester)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(
                post_body={"contents": {"en": _(
                    '%(followed_user_name)s · @%(followed_user_username)s has approved your follow request.') % {
                                                  'followed_user_username': followed_user.username,
                                                  'followed_user_name': followed_user.profile.name,
                                              }}})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.FOLLOW_REQUEST_APPROVED,
        }

        notification_group = NOTIFICATION_GROUP_MEDIUM_PRIORITY

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(user=follow_requester, notification=one_signal_notification)


def send_connection_request_push_notification(connection_requester, connection_requested_for):
    if connection_requested_for.has_connection_request_notifications_enabled():
        target_user_language_code = get_notification_language_code_for_target_user(connection_requested_for)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(
                post_body={"contents": {"en": _(
                    '%(connection_requester_name)s · @%(connection_requester_username)s wants to connect with you.') % {
                                                  'connection_requester_username': connection_requester.username,
                                                  'connection_requester_name': connection_requester.profile.name,
                                              }}})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.CONNECTION_REQUEST,
        }

        notification_group = NOTIFICATION_GROUP_MEDIUM_PRIORITY

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(user=connection_requested_for, notification=one_signal_notification)


def send_post_comment_reaction_push_notification(post_comment_reaction):
    post_comment_commenter = post_comment_reaction.post_comment.commenter

    notification_group = NOTIFICATION_GROUP_LOW_PRIORITY

    post_comment_reactor = post_comment_reaction.reactor
    target_user_language_code = get_notification_language_code_for_target_user(post_comment_commenter)
    with translation.override(target_user_language_code):
        one_signal_notification = onesignal_sdk.Notification(post_body={
            "contents": {
                "en": _(
                    '%(post_comment_reactor_name)s · @%(post_comment_reactor_username)s reacted to your comment.') % {
                          'post_comment_reactor_name': post_comment_reactor.profile.name,
                          'post_comment_reactor_username': post_comment_reactor.username,
                      }}
        })
    Notification = get_notification_model()
    notification_data = {
        'type': Notification.POST_COMMENT_REACTION,
    }
    one_signal_notification.set_parameter('data', notification_data)
    one_signal_notification.set_parameter('!thread_id', notification_group)
    one_signal_notification.set_parameter('android_group', notification_group)
    _send_notification_to_user(notification=one_signal_notification, user=post_comment_commenter)


def send_post_comment_user_mention_push_notification(post_comment_user_mention):
    mentioned_user = post_comment_user_mention.user

    if not mentioned_user.has_post_comment_mention_notifications_enabled():
        return

    notification_group = NOTIFICATION_GROUP_MEDIUM_PRIORITY

    mentioner = post_comment_user_mention.post_comment.commenter

    target_user_language_code = get_notification_language_code_for_target_user(mentioned_user)
    with translation.override(target_user_language_code):
        one_signal_notification = onesignal_sdk.Notification(post_body={
            "contents": {
                "en": _(
                    '%(mentioner_name)s · @%(mentioner_username)s mentioned you in a comment.') % {
                          'mentioner_name': mentioner.profile.name,
                          'mentioner_username': mentioner.username,
                      }}
        })

    Notification = get_notification_model()
    notification_data = {
        'type': Notification.POST_COMMENT_USER_MENTION,
    }
    one_signal_notification.set_parameter('data', notification_data)
    one_signal_notification.set_parameter('!thread_id', notification_group)
    one_signal_notification.set_parameter('android_group', notification_group)
    _send_notification_to_user(notification=one_signal_notification, user=mentioned_user)


def send_post_user_mention_push_notification(post_user_mention):
    mentioned_user = post_user_mention.user

    if not mentioned_user.has_post_mention_notifications_enabled():
        return

    notification_group = NOTIFICATION_GROUP_MEDIUM_PRIORITY

    mentioner = post_user_mention.post.creator

    target_user_language_code = get_notification_language_code_for_target_user(mentioned_user)
    with translation.override(target_user_language_code):
        one_signal_notification = onesignal_sdk.Notification(post_body={
            "contents": {
                "en": _(
                    '%(mentioner_name)s · @%(mentioner_username)s mentioned you in a post.') % {
                          'mentioner_name': mentioner.profile.name,
                          'mentioner_username': mentioner.username,
                      }}
        })

    Notification = get_notification_model()
    notification_data = {
        'type': Notification.POST_USER_MENTION,
    }
    one_signal_notification.set_parameter('data', notification_data)
    one_signal_notification.set_parameter('!thread_id', notification_group)
    one_signal_notification.set_parameter('android_group', notification_group)
    _send_notification_to_user(notification=one_signal_notification, user=mentioned_user)


def send_community_invite_push_notification(community_invite):
    invited_user = community_invite.invited_user

    if invited_user.has_community_invite_notifications_enabled():
        invite_creator = community_invite.creator
        community = community_invite.community
        target_user_language_code = get_notification_language_code_for_target_user(invited_user)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(
                post_body={"contents": {"en": _(
                    '%(invite_creator_name)s · @%(invite_creator_username)s has invited you to join c/%(community_name)s.') % {
                                                  'invite_creator_username': invite_creator.username,
                                                  'invite_creator_name': invite_creator.profile.name,
                                                  'community_name': community.name,
                                              }}})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.COMMUNITY_INVITE,
        }

        notification_group = NOTIFICATION_GROUP_MEDIUM_PRIORITY

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(notification=one_signal_notification, user=invited_user)


def send_community_new_post_push_notification(community_notifications_subscription):
    community_name = community_notifications_subscription.community.name
    target_user = community_notifications_subscription.subscriber

    if target_user.has_community_new_post_notifications_enabled():
        target_user_language_code = get_notification_language_code_for_target_user(target_user)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(
                post_body={"contents": {"en": _('A new post was posted in c/%(community_name)s.') % {
                    'community_name': community_name,
                }}})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.COMMUNITY_NEW_POST,
        }

        notification_group = NOTIFICATION_GROUP_HIGH_PRIORITY

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(notification=one_signal_notification, user=target_user)


def send_user_new_post_push_notification(user_notifications_subscription, post):
    post_creator_name = user_notifications_subscription.user.profile.name
    post_creator_username = user_notifications_subscription.user.username
    target_user = user_notifications_subscription.subscriber

    if target_user.has_user_new_post_notifications_enabled():
        target_user_language_code = get_notification_language_code_for_target_user(target_user)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(
                post_body={
                    "contents": {"en": _('%(post_creator_name)s · @%(post_creator_username)s posted something.') % {
                        'post_creator_username': post_creator_username,
                        'post_creator_name': post_creator_name,
                    }}})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.USER_NEW_POST,
        }
        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(notification=one_signal_notification, user=target_user)


def get_notification_language_code_for_target_user(target_user):
    if target_user.language and translation.check_for_language(target_user.language.code):
        return target_user.language.code

    return translation_strategy.get_default_translation_language_code()


def _send_notification_to_user(user, notification):
    send_notification_to_user_with_id.delay(user_id=user.pk, notification=notification)
