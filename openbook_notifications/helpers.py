import django_rq
from django.utils.translation import ugettext_lazy as _
import onesignal as onesignal_sdk

from openbook_common.utils.model_loaders import get_notification_model
from openbook_notifications.django_rq_jobs import send_notification_to_user

import logging

logger = logging.getLogger(__name__)


def send_post_reaction_push_notification(post_reaction):
    post_creator = post_reaction.post.creator

    post_id = post_reaction.post_id
    notification_group = 'post_%s' % post_id

    if post_creator.has_reaction_notifications_enabled_for_post_with_id(post_id=post_reaction.post_id):
        post_reactor = post_reaction.reactor

        one_signal_notification = onesignal_sdk.Notification(post_body={
            "contents": {"en": _('@%(post_reactor_username)s reacted to your post.') % {
                'post_reactor_username': post_reactor.username
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

    post = post_comment.post

    notification_group = 'post_%s' % post.id

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
        one_signal_notification = onesignal_sdk.Notification(post_body={
            "contents": {"en": _('@%(following_user_username)s started following you') % {
                'following_user_username': following_user.username
            }}
        })

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.FOLLOW,
        }

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(notification=one_signal_notification, user=followed_user)


def send_connection_request_push_notification(connection_requester, connection_requested_for):
    if connection_requested_for.has_connection_request_notifications_enabled():
        one_signal_notification = onesignal_sdk.Notification(
            post_body={"en": _('@%(connection_requester_username)s wants to connect with you.') % {
                'connection_requester_username': connection_requester.username
            }})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.CONNECTION_REQUEST,
        }

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(user=connection_requested_for, notification=one_signal_notification, )


def send_post_comment_reaction_push_notification(post_comment_reaction):
    post_comment_commenter = post_comment_reaction.post_comment.commenter

    post_comment_id = post_comment_reaction.post_comment_id
    notification_group = 'post_comment_%s' % post_comment_id

    post_comment_reactor = post_comment_reaction.reactor
    one_signal_notification = onesignal_sdk.Notification(post_body={
        "contents": {"en": _('@%(post_comment_reactor_username)s reacted to your comment.') % {
            'post_comment_reactor_username': post_comment_reactor.username
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


def send_community_invite_push_notification(community_invite):
    invited_user = community_invite.invited_user

    if invited_user.has_community_invite_notifications_enabled():
        invite_creator = community_invite.creator
        community = community_invite.community

        one_signal_notification = onesignal_sdk.Notification(
            post_body={"en": _('@%(invite_creator)s has invited you to join /c/%(community_name)s.') % {
                'invite_creator': invite_creator.username,
                'community_name': community.name,
            }})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.COMMUNITY_INVITE,
        }

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(notification=one_signal_notification, user=invited_user)


def _send_notification_to_user(user, notification):
    django_rq.enqueue(send_notification_to_user, user=user, notification=notification)
