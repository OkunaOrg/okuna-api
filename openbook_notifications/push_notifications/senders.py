import onesignal as onesignal_sdk
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from onesignal import OneSignalError

from openbook_common.utils.model_loaders import get_notification_model, get_user_model, get_post_model
from openbook_notifications.push_notifications.serializers import PushNotificationsSerializers
from hashlib import sha256

import logging

logger = logging.getLogger(__name__)

onesignal_client = onesignal_sdk.Client(
    app_id=settings.ONE_SIGNAL_APP_ID,
    app_auth_key=settings.ONE_SIGNAL_API_KEY
)


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

        NotificationPostReactionSerializer = _get_push_notifications_serializers().NotificationPostReactionSerializer

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.POST_REACTION,
            'payload': NotificationPostReactionSerializer(post_reaction).data
        }

        one_signal_notification.set_parameter('data', notification_data)
        one_signal_notification.set_parameter('!thread_id', notification_group)
        one_signal_notification.set_parameter('android_group', notification_group)

        _send_notification_to_user(notification=one_signal_notification, user=post_creator)


def send_post_comment_push_notification_with_message(post_comment, message, target_user):
    Notification = get_notification_model()
    NotificationPostCommentSerializer = _get_push_notifications_serializers().NotificationPostCommentSerializer

    post = post_comment.post

    notification_payload = NotificationPostCommentSerializer(post_comment).data
    notification_group = 'post_%s' % post.id

    one_signal_notification = onesignal_sdk.Notification(post_body={
        "contents": message
    })

    notification_data = {
        'type': Notification.POST_COMMENT,
        'payload': notification_payload
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

        FollowNotificationSerializer = _get_push_notifications_serializers().FollowNotificationSerializer

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.FOLLOW,
            'payload': FollowNotificationSerializer({
                'following_user': following_user
            }).data
        }

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(notification=one_signal_notification, user=followed_user)


def send_connection_request_push_notification(connection_requester, connection_requested_for):
    if connection_requested_for.has_connection_request_notifications_enabled():
        one_signal_notification = onesignal_sdk.Notification(
            post_body={"en": _('@%(connection_requester_username)s wants to connect with you.') % {
                'connection_requester_username': connection_requester.username
            }})

        ConnectionRequestNotificationSerializer = _get_push_notifications_serializers().ConnectionRequestNotificationSerializer

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.CONNECTION_REQUEST,
            'payload': ConnectionRequestNotificationSerializer({
                'connection_requester': connection_requester
            }).data
        }

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(user=connection_requested_for, notification=one_signal_notification, )


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

        NotificationCommunityInviteSerializer = _get_push_notifications_serializers().NotificationCommunityInviteSerializer

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.COMMUNITY_INVITE,
            'payload': NotificationCommunityInviteSerializer(community_invite).data
        }

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(notification=one_signal_notification, user=invited_user)


def _send_notification_to_user(user, notification):
    for device in user.devices.all():
        notification.set_parameter('ios_badgeType', 'Increase')
        notification.set_parameter('ios_badgeCount', '1')

        user_id_contents = (str(user.uuid) + str(user.id)).encode('utf-8')

        user_id = sha256(user_id_contents).hexdigest()

        notification.set_filters([
            {"field": "tag", "key": "user_id", "relation": "=", "value": user_id},
            {"field": "tag", "key": "device_uuid", "relation": "=", "value": device.uuid},
        ])

        try:
            onesignal_client.send_notification(notification)
        except OneSignalError as e:
            logger.error('Error sending notification to user_id %s with error %s' % (user.id, e))


push_notifications_serializers = None


def _get_push_notifications_serializers():
    global push_notifications_serializers

    if not push_notifications_serializers:
        push_notifications_serializers = PushNotificationsSerializers()
    return push_notifications_serializers
