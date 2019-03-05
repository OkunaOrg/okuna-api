import onesignal as onesignal_sdk
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_notification_model
from openbook_notifications.push_notifications.serializers import PushNotificationsSerializers

onesignal_client = onesignal_sdk.Client(
    app={"app_auth_key": settings.ONE_SIGNAL_API_KEY, "app_id": settings.ONE_SIGNAL_APP_ID})


def send_post_reaction_push_notification(post_reaction):
    post_creator = post_reaction.post.creator

    if post_creator.has_post_reaction_notifications_enabled():
        post_reactor = post_reaction.reactor

        one_signal_notification = onesignal_sdk.Notification(
            contents={"en": _('@%(post_reactor_username)s reacted to your post.') % {
                'post_reactor_username': post_reactor.username
            }})

        NotificationPostReactionSerializer = _get_push_notifications_serializers().NotificationPostReactionSerializer

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.POST_REACTION,
            'payload': NotificationPostReactionSerializer(post_reaction).data
        }

        one_signal_notification.set_parameter('data', notification_data)

        target_devices = post_creator.get_devices_one_signal_player_ids()

        _send_notification_to_target_devices(notification=one_signal_notification, target_devices=target_devices)


def send_post_comment_push_notification(post_comment):
    post_creator = post_comment.post.creator

    if post_creator.has_post_comment_notifications_enabled():
        post_commenter = post_comment.commenter

        one_signal_notification = onesignal_sdk.Notification(
            contents={"en": _('@%(post_commenter_username)s commented on your post.') % {
                'post_commenter_username': post_commenter.username
            }})

        NotificationPostCommentSerializer = _get_push_notifications_serializers().NotificationPostCommentSerializer

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.POST_COMMENT,
            'payload': NotificationPostCommentSerializer(post_comment).data
        }

        one_signal_notification.set_parameter('data', notification_data)

        target_devices = post_creator.get_devices_one_signal_player_ids()

        _send_notification_to_target_devices(notification=one_signal_notification, target_devices=target_devices)


def send_follow_push_notification(followed_user, following_user):
    if followed_user.has_follow_notifications_enabled():
        one_signal_notification = onesignal_sdk.Notification(
            contents={"en": _('@%(following_user_username)s started following you') % {
                'following_user_username': following_user.username
            }})

        FollowNotificationSerializer = _get_push_notifications_serializers().FollowNotificationSerializer

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.FOLLOW,
            'payload': FollowNotificationSerializer({
                'following_user': following_user
            }).data
        }

        one_signal_notification.set_parameter('data', notification_data)

        target_devices = followed_user.get_devices_one_signal_player_ids()

        _send_notification_to_target_devices(notification=one_signal_notification, target_devices=target_devices)


def send_connection_request_push_notification(connection_requester, connection_requested_for):
    if connection_requested_for.has_connection_request_notifications_enabled():
        one_signal_notification = onesignal_sdk.Notification(
            contents={"en": _('@%(connection_requester_username)s wants to connect with you.') % {
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

        target_devices = connection_requested_for.get_devices_one_signal_player_ids()

        _send_notification_to_target_devices(notification=one_signal_notification, target_devices=target_devices)


def _send_notification_to_target_devices(notification, target_devices):
    if target_devices:
        notification.set_target_devices(target_devices)

        onesignal_response = onesignal_client.send_notification(notification)

        print(onesignal_response.status_code)
        print(onesignal_response.json())


push_notifications_serializers = None


def _get_push_notifications_serializers():
    global push_notifications_serializers

    if not push_notifications_serializers:
        push_notifications_serializers = PushNotificationsSerializers()
    return push_notifications_serializers
