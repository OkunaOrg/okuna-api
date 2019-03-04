import onesignal as onesignal_sdk
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

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

        target_devices = post_creator.get_devices_one_signal_player_ids()

        _send_notification_to_target_devices(notification=one_signal_notification, target_devices=target_devices)


def send_follow_push_notification(followed_user, following_user):
    if followed_user.has_follow_notifications_enabled():
        one_signal_notification = onesignal_sdk.Notification(
            contents={"en": _('@%(following_user_username)s started following you') % {
                'following_user_username': following_user.username
            }})
        target_devices = followed_user.get_devices_one_signal_player_ids()

        _send_notification_to_target_devices(notification=one_signal_notification, target_devices=target_devices)


def send_connection_request_push_notification(connection_requester, connection_requested_for):
    if connection_requested_for.has_connection_request_notifications_enabled():
        one_signal_notification = onesignal_sdk.Notification(
            contents={"en": _('@%(connection_requester_username)s wants to connect with you.') % {
                'connection_requester_username': connection_requester.username
            }})

        target_devices = connection_requested_for.get_devices_one_signal_player_ids()

        _send_notification_to_target_devices(notification=one_signal_notification, target_devices=target_devices)


def _send_notification_to_target_devices(notification, target_devices):
    if target_devices:
        notification.set_target_devices(target_devices)

        onesignal_response = onesignal_client.send_notification(notification)

        print(onesignal_response.status_code)
        print(onesignal_response.json())
