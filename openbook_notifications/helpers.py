import django_rq
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
import onesignal as onesignal_sdk

from openbook_common.utils.model_loaders import get_notification_model
from openbook_notifications.django_rq_jobs import send_notification_to_user_with_id
from openbook_translation import translation_strategy

import logging

logger = logging.getLogger(__name__)


def send_post_reaction_push_notification(post_reaction):
    post_creator = post_reaction.post.creator

    post_id = post_reaction.post_id
    notification_group = 'post_%s' % post_id

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

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(notification=one_signal_notification, user=followed_user)


def send_connection_request_push_notification(connection_requester, connection_requested_for):
    if connection_requested_for.has_connection_request_notifications_enabled():
        target_user_language_code = get_notification_language_code_for_target_user(connection_requested_for)
        with translation.override(target_user_language_code):
            one_signal_notification = onesignal_sdk.Notification(
                post_body={"en": _(
                    '%(connection_requester_name)s · @%(connection_requester_username)s wants to connect with you.') % {
                                     'connection_requester_username': connection_requester.username,
                                     'connection_requester_name': connection_requester.profile.name,
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

    post_comment_id = post_comment_user_mention.post_comment_id
    notification_group = 'post_comment_%s' % post_comment_id

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

    post_id = post_user_mention.post_id
    notification_group = 'post_%s' % post_id

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
                post_body={"en": _(
                    '%(invite_creator_name)s · @%(invite_creator_username)s has invited you to join /c/%(community_name)s.') % {
                                     'invite_creator_username': invite_creator.username,
                                     'invite_creator_name': invite_creator.profile.name,
                                     'community_name': community.name,
                                 }})

        Notification = get_notification_model()

        notification_data = {
            'type': Notification.COMMUNITY_INVITE,
        }

        one_signal_notification.set_parameter('data', notification_data)

        _send_notification_to_user(notification=one_signal_notification, user=invited_user)


def get_notification_language_code_for_target_user(target_user):
    if target_user.language is not None and translation.check_for_language(target_user.language.code):
        return target_user.language.code

    return translation_strategy.get_default_translation_language_code()


def _send_notification_to_user(user, notification):
    django_rq.enqueue(send_notification_to_user_with_id, user_id=user.pk, notification=notification)
