import jwt
from django.conf import settings
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound, AuthenticationFailed
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_post_model, get_community_model, get_post_comment_model, \
    get_language_model, get_user_model, get_emoji_group_model, get_post_reaction_model, get_user_invite_model, \
    get_community_notifications_subscription_model, get_user_notifications_subscription_model

from openbook_common import checkers as common_checkers


def check_follow_lists_ids(user, lists_ids):
    for list_id in lists_ids:
        check_follow_list_id(user=user, list_id=list_id)


def check_follow_list_id(user, list_id):
    check_has_list_with_id(user=user, list_id=list_id)


def check_can_update_post(user, post):
    check_has_post(user=user, post=post)
    if post.is_closed and post.community_id:
        if not user.is_staff_of_community_with_name(post.community.name):
            raise ValidationError(
                _('You cannot edit a closed post'),
            )


def check_can_post_to_circles_with_ids(user, circles_ids=None):
    for circle_id in circles_ids:
        if not user.has_circle_with_id(circle_id) and not user.is_world_circle_id(circle_id):
            raise ValidationError(
                _('You cannot post to circle with id %(id)s') % {'id': circle_id},
            )


def check_can_post_to_community_with_name(user, community_name=None):
    if not user.is_member_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('You cannot post to a community you\'re not member of '),
        )


def check_can_enable_disable_comments_for_post_in_community_with_name(user, community_name):
    if not user.is_moderator_of_community_with_name(community_name) and \
            not user.is_administrator_of_community_with_name(community_name):
        raise ValidationError(
            _('Only moderators/administrators can enable/disable comments'),
        )


def check_comments_enabled_for_post_with_id(user, post_id):
    Post = get_post_model()
    post = Post.objects.select_related('community').get(id=post_id)
    if post.community_id is not None:
        if not user.is_staff_of_community_with_name(post.community.name) and not post.comments_enabled:
            raise ValidationError(
                _('Comments are disabled for this post')
            )


def check_can_translate_post_with_id(user, post_id):
    Post = get_post_model()
    post = Post.objects.get(id=post_id)
    if post.is_encircled_post():
        raise ValidationError(
            _('Only public posts can be translated')
        )
    if post.text is None:
        raise ValidationError(
            _('Post has no text to be translated')
        )
    if post.language is None:
        raise ValidationError(
            _('Post has no assigned language to be able to translate')
        )
    if user.translation_language is None:
        raise ValidationError(
            _('User\'s preferred translation language not set')
        )


def check_can_open_post_with_id(user, post_id):
    Post = get_post_model()
    post = Post.objects.select_related('community').get(id=post_id)
    if post.community_id is None:
        raise ValidationError(
            _('Only community posts can be opened/closed')
        )

    if not user.is_staff_of_community_with_name(post.community.name):
        raise ValidationError(
            _('Only administrators/moderators can open this post')
        )


def check_can_close_post(user, post):
    if post.community_id is None:
        raise ValidationError(
            _('Only community posts can be opened/closed')
        )

    if not user.is_staff_of_community_with_name(post.community.name):
        raise ValidationError(
            _('Only administrators/moderators can close this post')
        )


def check_list_data(user, name):
    if name:
        check_list_name_not_taken(user=user, list_name=name)


def check_community_data(user, community, name=None, cover=None, avatar=None, type=None):
    if name:
        check_community_name_not_taken(user=user, community_name=name)

    if type:
        check_community_type_can_be_updated(type=type, community=community)


def check_community_type_can_be_updated(type, community):
    Community = get_community_model()
    if type == Community.COMMUNITY_TYPE_PUBLIC and community.is_private():
        raise ValidationError(
            _('A community cannot be changed from private to public'),
        )


def check_circle_data(user, name, color):
    if name:
        check_circle_name_not_taken(user=user, circle_name=name)


def check_can_create_follow_request(user, user_requesting_to_follow):
    check_can_follow_user(user=user, user_to_follow=user_requesting_to_follow, is_pre_approved=True)
    check_target_user_has_no_follow_request_from_user(user=user, target_user=user_requesting_to_follow)
    check_user_visibility_is_private(target_user=user_requesting_to_follow)


def check_can_delete_follow_request_for_user(user, user_requesting_to_follow):
    check_has_follow_request(user=user_requesting_to_follow, requesting_user=user)


def check_can_approve_follow_request_from_requesting_user(user, requesting_user):
    check_has_follow_request(user=user, requesting_user=requesting_user)


def check_can_delete_follow_request_from_requesting_user(user, requesting_user):
    check_has_follow_request(user=user, requesting_user=requesting_user)


def check_has_follow_request(user, requesting_user):
    if not user.has_follow_request_from_user(requesting_user):
        raise ValidationError('Follow request does not exist.')


def check_target_user_has_no_follow_request_from_user(user, target_user):
    if target_user.has_follow_request_from_user(user):
        raise ValidationError('Follow request already exists.')


def check_can_follow_user(user, user_to_follow, is_pre_approved):
    if user.pk == user_to_follow.pk:
        raise ValidationError(
            _('You cannot follow yourself.'),
        )

    check_is_not_following_user_with_id(user=user, user_id=user_to_follow.pk)
    check_is_not_blocked_with_user_with_id(user=user, user_id=user_to_follow.pk)
    check_has_not_reached_max_follows(user=user)

    if not is_pre_approved:
        check_user_visibility_is_not_private(target_user=user_to_follow)


def check_user_visibility_is_not_private(target_user):
    if target_user.has_visibility_private():
        raise ValidationError(
            _('This user is private.'),
        )


def check_user_visibility_is_not_okuna(target_user):
    if target_user.has_visibility_okuna():
        raise ValidationError(
            _('This user content is restricted to Okuna members only.'),
        )


def check_user_visibility_is_private(target_user):
    # Check wether the visibility is private
    if not target_user.has_visibility_private():
        raise ValidationError(
            _('This user is not private.'),
        )


def check_can_get_posts_for_user(user, target_user):
    check_target_user_is_visibile_for_user(user=user, target_user=target_user)


def check_target_user_is_visibile_for_user(user, target_user):
    if target_user.has_visibility_private() and not user.is_following_user(target_user):
        raise ValidationError(_('This user is private, send a follow request.'))


def check_can_get_unauthenticated_posts_for_user(user):
    check_user_visibility_is_not_private(target_user=user)
    check_user_visibility_is_not_okuna(target_user=user)


def check_is_not_following_user_with_id(user, user_id):
    if user.is_following_user_with_id(user_id):
        raise ValidationError(
            _('Already following user.'),
        )


def check_has_not_reached_max_follows(user):
    if user.count_following() >= settings.USER_MAX_FOLLOWS:
        raise ValidationError(
            _('Maximum number of follows reached.'),
        )


def check_is_not_following_user_with_id_in_list_with_id(user, user_id, list_id):
    check_is_following_user_with_id(user=user, user_id=user_id)

    if user.is_following_user_with_id_in_list_with_id(user_id, list_id):
        raise ValidationError(
            _('Already following user in list.'),
        )


def check_is_following_user_with_id_in_list_with_id(user, user_id, list_id):
    check_is_following_user_with_id(user=user, user_id=user_id)

    if not user.is_following_user_with_id_in_list_with_id(user_id, list_id):
        raise ValidationError(
            _('Not following user in list.'),
        )


def check_is_following_user_with_id(user, user_id):
    if not user.is_following_user_with_id(user_id):
        raise ValidationError(
            _('Not following user.'),
        )


def check_has_not_reached_max_connections(user):
    if user.count_connections() > settings.USER_MAX_CONNECTIONS:
        raise ValidationError(
            _('Maximum number of connections reached.'),
        )


def check_can_connect_with_target_user(user, user_to_connect_with):
    if user.pk == user_to_connect_with:
        raise ValidationError(
            _('A user cannot connect with itself.'),
        )

    check_target_user_is_visibile_for_user(user=user, target_user=user_to_connect_with)
    check_is_not_blocked_with_user_with_id(user=user, user_id=user_to_connect_with.pk)
    check_is_not_connected_with_user_with_id(user=user, user_id=user_to_connect_with.pk)
    check_has_not_reached_max_connections(user=user)


def check_is_not_connected_with_user_with_id(user, user_id):
    if user.is_connected_with_user_with_id(user_id):
        raise ValidationError(
            _('Already connected with user.'),
        )


def check_is_not_fully_connected_with_user_with_id(user, user_id):
    if user.is_fully_connected_with_user_with_id(user_id):
        raise ValidationError(
            _('Already fully connected with user.'),
        )


def check_is_connected_with_user_with_id(user, user_id):
    if not user.is_connected_with_user_with_id(user_id):
        raise ValidationError(
            _('Not connected with user.'),
        )


def check_is_connected_with_user_with_id_in_circle_with_id(user, user_id, circle_id):
    if not user.is_connected_with_user_with_id_in_circle_with_id(user_id, circle_id):
        raise ValidationError(
            _('Not connected with user in given circle.'),
        )


def check_is_not_connected_with_user_with_id_in_circle_with_id(user, user_id, circle_id):
    if user.is_connected_with_user_with_id_in_circle_with_id(user_id, circle_id):
        raise ValidationError(
            _('Already connected with user in given circle.'),
        )


def check_has_list_with_id(user, list_id):
    if not user.has_list_with_id(list_id):
        raise ValidationError(
            _('List does not exist.'),
        )


def check_has_circle_with_id(user, circle_id):
    if not user.has_circle_with_id(circle_id):
        raise ValidationError(
            _('Circle does not exist.'),
        )


def check_has_circles_with_ids(user, circles_ids):
    if not user.has_circles_with_ids(circles_ids):
        raise ValidationError(
            _('One or more of the circles do not exist.'),
        )


def check_can_delete_post(user, post):
    Post = get_post_model()

    if not user.has_post(post=post):
        if Post.is_post_with_id_a_community_post(post.pk):
            # If the comment is in a community, check if we're moderators
            if not user.is_moderator_of_community_with_name(
                    post.community.name) and not user.is_administrator_of_community_with_name(post.community.name):
                raise ValidationError(
                    _('Only moderators/administrators can remove community posts.'),
                )
            else:
                # TODO Not the best place to log this but doing the check for community again on delete is wasteful
                post.community.create_remove_post_log(source_user=user,
                                                      target_user=post.creator)
        else:
            raise ValidationError(
                _('You cannot remove a post that does not belong to you')
            )


def check_can_delete_list_with_id(user, list_id):
    if not user.has_list_with_id(list_id):
        raise ValidationError(
            _('Can\'t delete a list that does not belong to you.'),
        )


def check_can_update_list_with_id(user, list_id):
    if not user.has_list_with_id(list_id):
        raise ValidationError(
            _('Can\'t update a list that does not belong to you.'),
        )


def check_can_delete_community_with_name(user, community_name):
    if not user.is_creator_of_community_with_name(community_name):
        raise ValidationError(
            _('Can\'t delete a community that you do not administrate.'),
        )


def check_can_update_community_with_name(user, community_name):
    if not user.is_administrator_of_community_with_name(community_name):
        raise ValidationError(
            _('Can\'t update a community that you do not administrate.'),
        )


def check_can_get_posts_for_community_with_name(user, community_name):
    check_is_not_banned_from_community_with_name(user=user, community_name=community_name)
    Community = get_community_model()
    if Community.is_community_with_name_private(
            community_name=community_name) and not user.is_member_of_community_with_name(
        community_name=community_name):
        raise ValidationError(
            _('The community is private. You must become a member to retrieve its posts.'),
        )


def check_can_get_closed_posts_for_community_with_name(user, community_name):
    if not user.is_administrator_of_community_with_name(community_name=community_name) and \
            not user.is_moderator_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('Only administrators/moderators can view closed posts'),
        )


def check_can_enable_new_post_notifications_for_community(user, community):
    is_member = user.is_member_of_community_with_name(community_name=community.name)

    if not is_member:
        raise ValidationError(
            _('Only members can enable new post notifications'),
        )
    new_post_notifications_enabled = user.are_new_post_notifications_enabled_for_community(community=community)

    if new_post_notifications_enabled:
        raise ValidationError(
            _('New post notifications are already enabled'),
        )

    check_is_not_banned_from_community_with_name(user=user, community_name=community.name)


def check_can_disable_new_post_notifications_for_community(user, community):
    new_post_notifications_enabled = user.are_new_post_notifications_enabled_for_community(community=community)

    if not new_post_notifications_enabled:
        raise ValidationError(
            _('New post notifications are not enabled'),
        )


def check_can_get_community_with_name_members(user, community_name):
    check_is_not_banned_from_community_with_name(user=user, community_name=community_name)

    Community = get_community_model()

    if Community.is_community_with_name_private(community_name=community_name):
        if not user.is_member_of_community_with_name(community_name=community_name):
            raise ValidationError(
                _('Can\'t see the members of a private community.'),
            )


def check_can_join_community_with_name(user, community_name):
    if user.is_banned_from_community_with_name(community_name):
        raise ValidationError('You can\'t join a community you have been banned from.')

    if user.is_member_of_community_with_name(community_name):
        raise ValidationError(
            _('You are already a member of the community.'),
        )

    Community = get_community_model()
    if Community.is_community_with_name_private(community_name=community_name):
        if not user.is_invited_to_community_with_name(community_name=community_name):
            raise ValidationError(
                _('You are not invited to join this community.'),
            )


def check_can_leave_community_with_name(user, community_name):
    if not user.is_member_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('You cannot leave a community you\'re not part of.'),
        )

    if user.is_creator_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('You cannot leave a community you created.'),
        )


def check_can_invite_user_with_username_to_community_with_name(user, username, community_name):
    if not user.is_member_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('You can only invite people to a community you are member of.'),
        )

    if user.has_invited_user_with_username_to_community_with_name(username=username, community_name=community_name):
        raise ValidationError(
            _('You have already invited this user to join the community.'),
        )

    Community = get_community_model()

    if Community.is_user_with_username_member_of_community_with_name(username=username,
                                                                     community_name=community_name):
        raise ValidationError(
            _('The user is already part of the community.'),
        )

    if not Community.is_community_with_name_invites_enabled(community_name=community_name) and not (
            user.is_administrator_of_community_with_name(
                community_name=community_name) or user.is_moderator_of_community_with_name(
        community_name=community_name)):
        raise ValidationError(
            _('Invites for this community are not enabled. Only administrators & moderators can invite.'),
        )


def check_can_uninvite_user_with_username_to_community_with_name(user, username, community_name):
    if not user.has_invited_user_with_username_to_community_with_name(username=username,
                                                                      community_name=community_name):
        raise ValidationError(
            _('No invite to withdraw.'),
        )


def check_can_get_community_with_name_banned_users(user, community_name):
    if not user.is_administrator_of_community_with_name(
            community_name=community_name) and not user.is_moderator_of_community_with_name(
        community_name=community_name):
        raise ValidationError(
            _('Only community administrators & moderators can get banned users.'),
        )


def check_can_ban_user_with_username_from_community_with_name(user, username, community_name):
    if not user.is_administrator_of_community_with_name(
            community_name=community_name) and not user.is_moderator_of_community_with_name(
        community_name=community_name):
        raise ValidationError(
            _('Only community administrators & moderators can ban community members.'),
        )

    Community = get_community_model()
    if Community.is_user_with_username_banned_from_community_with_name(username=username,
                                                                       community_name=community_name):
        raise ValidationError(
            _('User is already banned'),
        )

    if Community.is_user_with_username_moderator_of_community_with_name(username=username,
                                                                        community_name=community_name) or Community.is_user_with_username_administrator_of_community_with_name(
        username=username, community_name=community_name):
        raise ValidationError(
            _('You can\'t ban moderators or administrators of the community'),
        )


def check_can_unban_user_with_username_from_community_with_name(user, username, community_name):
    if not user.is_administrator_of_community_with_name(
            community_name=community_name) and not user.is_moderator_of_community_with_name(
        community_name=community_name):
        raise ValidationError(
            _('Only community administrators & moderators can ban community members.'),
        )

    Community = get_community_model()
    if not Community.is_user_with_username_banned_from_community_with_name(username=username,
                                                                           community_name=community_name):
        raise ValidationError(
            _('Can\'t unban a not-banned user.'),
        )


def check_can_add_administrator_with_username_to_community_with_name(user, username, community_name):
    if not user.is_creator_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('Only the creator of the community can add other administrators.'),
        )

    Community = get_community_model()

    if Community.is_user_with_username_administrator_of_community_with_name(username=username,
                                                                            community_name=community_name):
        raise ValidationError(
            _('User is already an administrator.'),
        )

    if not Community.is_user_with_username_member_of_community_with_name(username=username,
                                                                         community_name=community_name):
        raise ValidationError(
            _('Can\'t make administrator a user that is not part of the community.'),
        )


def check_can_remove_administrator_with_username_to_community_with_name(user, username, community_name):
    if not user.is_creator_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('Only the creator of the community can remove other administrators.'),
        )

    Community = get_community_model()

    if not Community.is_user_with_username_administrator_of_community_with_name(username=username,
                                                                                community_name=community_name):
        raise ValidationError(
            _('User to remove is not an administrator.'),
        )


def check_can_get_community_with_name_administrators(user, community_name):
    check_is_not_banned_from_community_with_name(user=user, community_name=community_name)


def check_can_add_moderator_with_username_to_community_with_name(user, username, community_name):
    if not user.is_administrator_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('Only administrators of the community can add other moderators.'),
        )

    Community = get_community_model()

    if Community.is_user_with_username_administrator_of_community_with_name(username=username,
                                                                            community_name=community_name):
        raise ValidationError(
            _('User is an administrator.'),
        )

    if Community.is_user_with_username_moderator_of_community_with_name(username=username,
                                                                        community_name=community_name):
        raise ValidationError(
            _('User is already a moderator.'),
        )

    if not Community.is_user_with_username_member_of_community_with_name(username=username,
                                                                         community_name=community_name):
        raise ValidationError(
            _('Can\'t make moderator a user that is not part of the community.'),
        )


def check_can_remove_moderator_with_username_to_community_with_name(user, username, community_name):
    if not user.is_administrator_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('Only administrators of the community can remove other moderators.'),
        )

    Community = get_community_model()
    if not Community.is_user_with_username_moderator_of_community_with_name(username=username,
                                                                            community_name=community_name):
        raise ValidationError(
            _('User to remove is not an moderator.'),
        )


def check_can_get_community_with_name_moderators(user, community_name):
    check_is_not_banned_from_community_with_name(user=user, community_name=community_name)


def check_is_not_banned_from_community_with_name(user, community_name):
    if user.is_banned_from_community_with_name(community_name):
        raise PermissionDenied('You have been banned from this community.')


def check_can_get_user_with_id(user, user_id):
    check_is_not_blocked_with_user_with_id(user=user, user_id=user_id)


def check_can_update_circle_with_id(user, circle_id):
    if not user.has_circle_with_id(circle_id):
        raise ValidationError(
            _('Can\'t update a circle that does not belong to you.'),
        )

    if user.is_world_circle_id(circle_id):
        raise ValidationError(
            _('Can\'t update the world circle.'),
        )

    if user.is_connections_circle_id(circle_id):
        raise ValidationError(
            _('Can\'t update the connections circle.'),
        )


def check_can_delete_circle_with_id(user, circle_id):
    if not user.has_circle_with_id(circle_id):
        raise ValidationError(
            _('Can\'t delete a circle that does not belong to you.'),
        )

    if user.is_world_circle_id(circle_id):
        raise ValidationError(
            _('Can\'t delete the world circle.'),
        )

    if user.is_connections_circle_id(circle_id):
        raise ValidationError(
            _('Can\'t delete the connections circle.'),
        )


def check_can_get_circle_with_id(user, circle_id):
    if not user.has_circle_with_id(circle_id):
        raise ValidationError(
            _('Can\'t view a circle that does not belong to you.'),
        )


def check_can_get_list_with_id(user, list_id):
    if not user.has_list_with_id(list_id):
        raise ValidationError(
            _('Can\'t view a list that does not belong to you.'),
        )


def check_circle_name_not_taken(user, circle_name):
    if user.has_circle_with_name(circle_name):
        raise ValidationError(
            _('You already have a circle with that name.'),
        )


def check_list_name_not_taken(user, list_name):
    if user.has_list_with_name(list_name):
        raise ValidationError(
            _('You already have a list with that name.'),
        )


def check_can_create_community_with_name(user, name):
    check_community_name_not_taken(user=user, community_name=name)


def check_community_name_not_taken(user, community_name):
    Community = get_community_model()
    if Community.is_name_taken(community_name):
        raise ValidationError(
            _('A community with that name already exists.'),
        )


def check_can_favorite_community_with_name(user, community_name):
    if not user.is_member_of_community_with_name(community_name=community_name):
        raise ValidationError(
            _('You must be member of a community before making it a favorite.'),
        )

    if user.has_favorite_community_with_name(community_name=community_name):
        raise ValidationError(
            _('You have already marked this community as favorite.'),
        )


def check_can_exclude_community_from_top_posts(user, community):
    if user.has_excluded_community_with_name_from_top_posts(community_name=community.name):
        raise ValidationError(
            _('You have already marked this community as excluded.'),
        )
    Community = get_community_model()
    if community.type == Community.COMMUNITY_TYPE_PRIVATE:
        raise ValidationError(
            _('Private communities are always excluded from top posts.'),
        )


def check_can_remove_top_posts_exclusion_for_community(user, community):
    if not user.has_excluded_community_with_name_from_top_posts(community_name=community.name):
        raise ValidationError(
            _('You have not marked this community as excluded.'),
        )


def check_can_exclude_community_from_profile_posts(user, community):
    if user.has_excluded_community_with_name_from_profile_posts(community_name=community.name):
        raise ValidationError(
            _('You have already marked this community as excluded.'),
        )


def check_can_remove_profile_posts_exclusion_for_community(user, community):
    if not user.has_excluded_community_with_name_from_profile_posts(community_name=community.name):
        raise ValidationError(
            _('You have not marked this community as excluded.'),
        )


def check_can_unfavorite_community_with_name(user, community_name):
    if not user.has_favorite_community_with_name(community_name=community_name):
        raise ValidationError(
            _('You have not favorited the community.'),
        )


def check_can_read_notification_with_id(user, notification_id):
    if not user.has_notification_with_id(notification_id=notification_id):
        raise ValidationError(
            _('You cannot mark as read a notification that doesn\'t belong to you.'),
        )


def check_can_delete_notification_with_id(user, notification_id):
    check_has_notification_with_id(user=user, notification_id=notification_id)


def check_has_notification_with_id(user, notification_id):
    if not user.has_notification_with_id(notification_id=notification_id):
        raise ValidationError(
            _('This notification does not belong to you.'),
        )


def check_can_update_device_with_uuid(user, device_uuid):
    check_has_device_with_uuid(user=user, device_uuid=device_uuid)


def check_can_delete_device_with_uuid(user, device_uuid):
    check_has_device_with_uuid(user=user, device_uuid=device_uuid)


def check_can_get_device_with_uuid(user, device_uuid):
    check_has_device_with_uuid(user=user, device_uuid=device_uuid)


def check_has_device_with_uuid(user, device_uuid):
    if not user.has_device_with_uuid(device_uuid=device_uuid):
        raise NotFound(
            _('Device not found'),
        )


def check_can_mute_post(user, post):
    if user.has_muted_post_with_id(post_id=post.pk):
        raise ValidationError(
            _('Post already muted'),
        )
    check_can_see_post(user=user, post=post)


def check_can_unmute_post(user, post):
    check_has_muted_post_with_id(post_id=post.pk, user=user)
    check_can_see_post(user=user, post=post)


def check_has_muted_post_with_id(user, post_id):
    if not user.has_muted_post_with_id(post_id=post_id):
        raise ValidationError(
            _('Post is not muted'),
        )


def check_can_mute_post_comment(user, post_comment):
    if user.has_muted_post_comment_with_id(post_comment_id=post_comment.pk):
        raise ValidationError(
            _('Post comment already muted'),
        )

    check_can_see_post_comment(user=user, post_comment=post_comment)


def check_can_unmute_post_comment(user, post_comment):
    check_has_muted_post_comment_with_id(user=user, post_comment_id=post_comment.pk)
    check_can_see_post_comment(user=user, post_comment=post_comment)


def check_has_muted_post_comment_with_id(user, post_comment_id):
    if not user.has_muted_post_comment_with_id(post_comment_id=post_comment_id):
        raise ValidationError(
            _('Post_comment is not muted'),
        )


def check_can_translate_comment_with_id(user, post_comment_id):
    PostComment = get_post_comment_model()
    post_comment = PostComment.objects.get(pk=post_comment_id)
    if post_comment.post.is_encircled_post():
        raise ValidationError(
            _('Only public post comments can be translated')
        )
    if post_comment.text is None:
        raise ValidationError(
            _('Post comment has no text to be translated')
        )
    if post_comment.language is None:
        raise ValidationError(
            _('Post comment has no assigned language to be able to translate')
        )
    if user.translation_language is None:
        raise ValidationError(
            _('User\'s preferred translation language not set')
        )


def check_has_post(user, post):
    if not user.has_post(post=post):
        raise PermissionDenied(
            _('This post does not belong to you.'),
        )


def check_password_matches(user, password):
    if not user.check_password(password):
        raise AuthenticationFailed(
            _('Wrong password.'),
        )


def check_device_with_uuid_does_not_exist(user, device_uuid):
    if user.devices.filter(uuid=device_uuid).exists():
        raise ValidationError('Device already exists')


def check_can_accept_guidelines(user):
    if user.are_guidelines_accepted:
        raise ValidationError('Guidelines were already accepted')


def check_can_set_language_with_id(user, language_id):
    Language = get_language_model()
    if not Language.objects.filter(pk=language_id).exists():
        raise ValidationError('Please provide a valid language id')


def check_can_get_community_with_name(user, community_name):
    check_is_not_banned_from_community_with_name(user=user, community_name=community_name)


def check_can_block_user_with_id(user, user_id):
    if user_id == user.pk:
        raise ValidationError(_('You cannot block yourself.'))
    check_is_not_blocked_with_user_with_id(user=user, user_id=user_id)


def check_can_unblock_user_with_id(user, user_id):
    if not user.has_blocked_user_with_id(user_id=user_id):
        raise ValidationError(_('You cannot unblock an account you have not blocked.'))


def check_is_not_blocked_with_user_with_id(user, user_id):
    """
    Checks that there is not a block between us and the given user_id
    """
    if user.is_blocked_with_user_with_id(user_id=user_id):
        raise PermissionDenied(_('This account is blocked.'))


def check_can_report_comment_for_post(user, post_comment, post):
    check_has_not_reported_post_comment_with_id(user=user, post_comment_id=post_comment.pk)
    check_can_see_post(user=user, post=post)

    if post_comment.commenter_id == user.pk:
        raise ValidationError(
            _('You cannot report your own comment.'),
        )


def check_has_not_reported_post_comment_with_id(user, post_comment_id):
    if user.has_reported_post_comment_with_id(post_comment_id=post_comment_id):
        raise ValidationError(
            _('You have already reported the comment.'),
        )


def check_can_report_post(user, post):
    check_can_see_post(user=user, post=post)
    check_has_not_reported_post_with_id(user=user, post_id=post.pk)
    if post.creator_id == user.pk:
        raise ValidationError(
            _('You cannot report your own post.'),
        )


def check_has_not_reported_post_with_id(user, post_id):
    if user.has_reported_post_with_id(post_id=post_id):
        raise ValidationError(
            _('You have already reported the post.'),
        )


def check_can_report_user(user, user_to_report):
    check_has_not_reported_user_with_id(user=user, user_id=user_to_report.pk)
    if user.pk == user_to_report.pk:
        raise ValidationError(
            _('You cannot report yourself...'),
        )


def check_has_not_reported_user_with_id(user, user_id):
    if user.has_reported_user_with_id(user_id=user_id):
        raise ValidationError(
            _('You have already reported the user.'),
        )


def check_can_report_community(user, community):
    check_has_not_reported_community_with_id(user=user, community_id=community.pk)
    if community.creator.pk == user.pk:
        raise ValidationError(
            _('You cannot report your own community.'),
        )


def check_has_not_reported_community_with_id(user, community_id):
    if user.has_reported_community_with_id(community_id=community_id):
        raise ValidationError(
            _('You have already reported the community.'),
        )


def check_can_report_hashtag(user, hashtag):
    check_has_not_reported_hashtag_with_id(user=user, hashtag_id=hashtag.pk)


def check_has_not_reported_hashtag_with_id(user, hashtag_id):
    if user.has_reported_hashtag_with_id(hashtag_id=hashtag_id):
        raise ValidationError(
            _('You have already reported the hashtag.'),
        )


def check_password_reset_verification_token_is_valid(user, password_verification_token):
    try:
        token_contents = jwt.decode(password_verification_token, settings.SECRET_KEY,
                                    algorithm=settings.JWT_ALGORITHM)

        token_user_id = token_contents['user_id']
        token_type = token_contents['type']

        if token_type != user.JWT_TOKEN_TYPE_PASSWORD_RESET:
            raise ValidationError(
                _('Token type does not match')
            )

        if token_user_id != user.pk:
            raise ValidationError(
                _('Token user id does not match')
            )
        return token_user_id
    except jwt.InvalidSignatureError:
        raise ValidationError(
            _('Invalid token signature')
        )
    except jwt.ExpiredSignatureError:
        raise ValidationError(
            _('Token expired')
        )
    except jwt.DecodeError:
        raise ValidationError(
            _('Failed to decode token')
        )
    except KeyError:
        raise ValidationError(
            _('Invalid token')
        )


def check_email_verification_token_is_valid_for_email(user, email_verification_token):
    try:
        token_contents = jwt.decode(email_verification_token, settings.SECRET_KEY,
                                    algorithm=settings.JWT_ALGORITHM)
        token_email = token_contents['email']
        new_email = token_contents['new_email']
        token_user_id = token_contents['user_id']
        token_type = token_contents['type']

        if token_type != user.JWT_TOKEN_TYPE_CHANGE_EMAIL:
            raise ValidationError(
                _('Token type does not match')
            )

        if token_email != user.email:
            raise ValidationError(
                _('Token email does not match')
            )

        if token_user_id != user.pk:
            raise ValidationError(
                _('Token user id does not match')
            )
        return new_email
    except jwt.InvalidSignatureError:
        raise ValidationError(
            _('Invalid token signature')
        )
    except jwt.ExpiredSignatureError:
        raise ValidationError(
            _('Token expired')
        )
    except jwt.DecodeError:
        raise ValidationError(
            _('Failed to decode token')
        )
    except KeyError:
        raise ValidationError(
            _('Invalid token')
        )


def check_connection_circles_ids(user, circles_ids):
    for circle_id in circles_ids:
        check_connection_circle_id(user=user, circle_id=circle_id)


def check_connection_circle_id(user, circle_id):
    check_has_circle_with_id(user=user, circle_id=circle_id)

    if user.is_world_circle_id(circle_id):
        raise ValidationError(
            _('Can\'t connect in the world circle.'),
        )


def check_email_not_taken(user, email):
    if email == user.email:
        return

    User = get_user_model()

    if User.is_email_taken(email=email):
        raise ValidationError(
            _('The email is already taken.')
        )


def check_username_not_taken(user, username):
    if username == user.username:
        return

    User = get_user_model()

    if User.is_username_taken(username=username):
        raise ValidationError(
            _('The username is already taken.')
        )


def check_can_edit_comment_with_id_for_post(user, post_comment_id, post):
    check_can_see_post(user=user, post=post)
    # Check that the comment belongs to the post
    PostComment = get_post_comment_model()

    if not PostComment.objects.filter(id=post_comment_id, post_id=post.pk).exists():
        raise ValidationError(
            _('The comment does not belong to the specified post.')
        )

    if post.community and post.is_closed:
        is_administrator = user.is_administrator_of_community_with_name(post.community.name)
        is_moderator = user.is_moderator_of_community_with_name(post.community.name)
        if not is_moderator and not is_administrator:
            raise ValidationError(
                _('Only administrators/moderators can edit a closed post.')
            )


def check_has_post_comment_with_id(user, post_comment_id):
    if not user.posts_comments.filter(id=post_comment_id).exists():
        # The comment is not ours
        raise ValidationError(
            _('You cannot edit a comment that does not belong to you')
        )


def check_can_delete_comment_with_id_for_post(user, post_comment_id, post):
    check_can_see_post(user=user, post=post)

    # Check that the comment belongs to the post
    PostComment = get_post_comment_model()
    Post = get_post_model()

    if not PostComment.objects.filter(id=post_comment_id, post_id=post.pk).exists():
        raise ValidationError(
            _('The comment does not belong to the specified post.')
        )
    is_comment_creator = user.posts_comments.filter(id=post_comment_id).exists()

    if post.community:
        is_moderator = user.is_moderator_of_community_with_name(post.community.name)
        is_administrator = user.is_administrator_of_community_with_name(post.community.name)
        if not is_administrator and not is_moderator:
            if post.is_closed:
                raise ValidationError(
                    _('Only moderators/administrators can remove closed community posts.'),
                )
            elif not is_comment_creator:
                raise ValidationError(
                    _('You cannot remove a comment that does not belong to you')
                )
        else:
            # is admin or mod
            post_comment = PostComment.objects.select_related('commenter').get(pk=post_comment_id)
            if post_comment.parent_comment is not None:
                post.community.create_remove_post_comment_reply_log(source_user=user,
                                                                    target_user=post_comment.commenter)
            else:
                post.community.create_remove_post_comment_log(source_user=user,
                                                              target_user=post_comment.commenter)
    elif not post.creator_id == user.pk and not is_comment_creator:
        # not a community post
        raise ValidationError(
            _('You cannot remove a comment that does not belong to you')
        )


def check_can_get_comments_for_post(user, post):
    check_can_see_post(user=user, post=post)


def check_can_get_comment_replies_for_post_and_comment(user, post, post_comment):
    if post_comment.post_id != post.id:
        raise ValidationError(
            _('No comment found with given id for post with given uuid')
        )
    check_can_see_post(user=user, post=post_comment.post)


def check_can_comment_in_post(user, post):
    check_can_see_post(user=user, post=post)
    check_comments_enabled_for_post_with_id(user=user, post_id=post.id)


def check_can_reply_to_post_comment_for_post(user, post_comment, post):
    if post_comment.post_id != post.id:
        raise ValidationError(
            _('No comment found with given id for post with given uuid')
        )

    check_can_comment_in_post(user=user, post=post)
    if post_comment.parent_comment is not None:
        raise ValidationError(
            _('You can post a reply to a comment, not to an existing reply')
        )


def check_can_delete_reaction_with_id_for_post(user, post_reaction_id, post):
    check_can_see_post(user=user, post=post)
    # Check if the post belongs to us
    if user.has_post(post=post):
        # Check that the comment belongs to the post
        PostReaction = get_post_reaction_model()
        if not PostReaction.objects.filter(id=post_reaction_id, post_id=post.pk).exists():
            raise ValidationError(
                _('That reaction does not belong to the specified post.')
            )
        return

    if not user.post_reactions.filter(id=post_reaction_id).exists():
        raise ValidationError(
            _('Can\'t delete a reaction that does not belong to you.'),
        )


def check_can_get_reactions_for_post(user, post):
    check_can_see_post(user=user, post=post)


def check_can_get_reactions_for_post_comment(user, post_comment):
    return check_can_get_reactions_for_post(user=user, post=post_comment.post)


def check_can_react_with_emoji_id(user, emoji_id):
    EmojiGroup = get_emoji_group_model()

    if not EmojiGroup.objects.filter(emojis__id=emoji_id, is_reaction_group=True).exists():
        raise ValidationError(
            _('Not a valid emoji to react with'),
        )


def check_can_react_to_post(user, post):
    check_can_see_post(user=user, post=post)


def check_can_see_post(user, post):
    if not user.can_see_post(post):
        raise ValidationError(
            _('This post is private.'),
        )


def check_can_see_hashtag(user, hashtag):
    if not user.can_see_hashtag(hashtag):
        raise PermissionDenied(
            _('This hashtag is not  available.'),
        )


def check_can_react_to_post_comment(user, post_comment, emoji_id):
    check_can_react_with_emoji_id(user=user, emoji_id=emoji_id)
    check_can_see_post_comment(user=user, post_comment=post_comment)

    if post_comment.post.is_closed:
        raise ValidationError(
            _('Cant react to comments on a closed post.'),
        )


def check_can_delete_post_comment_reaction(user, post_comment_reaction):
    check_can_see_post_comment(user=user, post_comment=post_comment_reaction.post_comment)

    if post_comment_reaction.reactor_id != user.pk:
        raise ValidationError(
            _('Can\'t delete a comment reaction that does not belong to you.'),
        )


def check_can_see_post_comment(user, post_comment):
    check_can_see_post(user=user, post=post_comment.post)

    if not user.can_see_post_comment(post_comment=post_comment):
        raise ValidationError(
            _('This comment is private.'),
        )


def check_can_get_comment_for_post(user, post_comment, post, ):
    check_can_see_post_comment(user=user, post_comment=post_comment)


def check_can_get_global_moderated_objects(user):
    check_is_global_moderator(user=user)


def check_can_get_moderated_object(user, moderated_object):
    if user.is_global_moderator():
        return

    check_can_get_community_moderated_objects(user=user, community_name=moderated_object.community)


def check_can_get_community_moderated_objects(user, community_name):
    check_is_staff_of_community_with_name(user=user, community_name=community_name)


def check_has_not_reported_moderated_object_with_id(user, moderated_object_id):
    if user.has_reported_moderated_object_with_id(moderated_object_id=moderated_object_id):
        raise ValidationError(
            _('You have already reported the moderated_object.'),
        )


def check_can_update_moderated_object(user, moderated_object):
    check_can_moderate_moderated_object(user=user, moderated_object=moderated_object)

    if moderated_object.is_verified():
        raise PermissionDenied(
            _('The moderated object has been verified and can no longer be edited.')
        )

    if not moderated_object.is_pending() and not user.is_global_moderator():
        raise PermissionDenied(
            _('The moderated object has already been approved/rejected.')
        )


def check_can_approve_moderated_object(user, moderated_object):
    check_can_moderate_moderated_object(user=user, moderated_object=moderated_object)

    if moderated_object.is_verified():
        raise ValidationError(
            _('The moderated object has already been verified.')
        )


def check_can_reject_moderated_object(user, moderated_object):
    check_can_moderate_moderated_object(user=user, moderated_object=moderated_object)
    if moderated_object.is_verified():
        raise ValidationError(
            _('The moderated object has already been verified.')
        )


def check_can_unverify_moderated_object(user, moderated_object):
    check_is_global_moderator(user=user)
    if not moderated_object.is_verified():
        raise ValidationError(
            _('The moderated object has not been verified.')
        )


def check_can_verify_moderated_object(user, moderated_object):
    check_is_global_moderator(user=user)
    if moderated_object.is_verified():
        raise ValidationError(
            _('The moderated object is already verified.')
        )

    if moderated_object.is_pending():
        raise ValidationError(
            _('You cannot verify a moderated object with status pending. Please approve or reject it.')
        )


def check_can_moderate_moderated_object(user, moderated_object):
    content_object = moderated_object.content_object

    is_global_moderator = user.is_global_moderator()

    if is_global_moderator:
        return

    PostComment = get_post_comment_model()
    Post = get_post_model()

    if isinstance(content_object, Post):
        if content_object.community:
            if not user.is_staff_of_community_with_name(community_name=content_object.community.name):
                raise ValidationError(_('Only community staff can moderate community posts'))
        else:
            raise ValidationError(_('Only global moderators can moderate non-community posts'))
    elif isinstance(content_object, PostComment):
        if content_object.post.community:
            if not user.is_staff_of_community_with_name(community_name=content_object.post.community.name):
                raise ValidationError(_('Only community staff can moderate community post comments'))
        else:
            raise ValidationError(_('Only global moderators can moderate non-community post comments'))
    else:
        raise ValidationError(_('Non global moderators can only moderate posts and post comments.'))


def check_is_global_moderator(user):
    if not user.is_global_moderator():
        raise PermissionDenied(_('Not a global moderator.'))


def check_is_staff_of_community_with_name(user, community_name):
    if not user.is_staff_of_community_with_name(community_name=community_name):
        raise PermissionDenied(_('Not a community staff.'))


def check_can_create_invite(user, nickname):
    if user.invite_count == 0:
        raise ValidationError(_('You have no invites left'))

    UserInvite = get_user_invite_model()
    if UserInvite.objects.filter(invited_by=user, nickname=nickname).exists():
        raise ValidationError('Nickname already in use')


def check_can_update_invite(user, invite_id):
    check_is_creator_of_invite_with_id(user=user, invite_id=invite_id)


def check_can_send_email_invite_to_invite_id(user, invite_id, email):
    check_is_creator_of_invite_with_id(user=user, invite_id=invite_id)
    UserInvite = get_user_invite_model()
    invite = UserInvite.objects.get(id=invite_id)
    if invite.email == email:
        raise ValidationError(_('Invite email already sent to this address'))


def check_can_delete_invite_with_id(user, invite_id):
    check_is_creator_of_invite_with_id(user=user, invite_id=invite_id)
    check_if_invite_is_not_used(user=user, invite_id=invite_id)


def check_if_invite_is_not_used(user, invite_id):
    UserInvite = get_user_invite_model()
    invite = UserInvite.objects.get(id=invite_id)
    if invite.created_user:
        raise ValidationError(_('Invite is already used and cannot be deleted'))


def check_is_creator_of_invite_with_id(user, invite_id):
    UserInvite = get_user_invite_model()
    if not UserInvite.objects.filter(id=invite_id, invited_by=user).exists():
        raise ValidationError(_('Invite was not created by you'))


def check_can_add_media_to_post(user, post):
    check_has_post(user=user, post=post)


def check_can_publish_post(user, post):
    check_has_post(user=user, post=post)


def check_can_get_status_for_post(user, post):
    check_has_post(user=user, post=post)


def check_can_get_media_for_post(user, post):
    check_can_see_post(user=user, post=post)


def check_can_get_preview_link_data_for_post(user, post):
    check_can_see_post(post=post, user=user)
    if not post.has_links():
        raise ValidationError(
            _('No link associated with post.'),
        )


def check_can_enable_new_post_notifications_for_user(user, target_user):
    if user.username == target_user.username:
        raise ValidationError(
            _('You cannot enable notifications for yourself'),
        )

    new_post_notifications_enabled = user.are_new_post_notifications_enabled_for_user(user=target_user)

    if target_user.has_blocked_user_with_id(user_id=user.pk) or user.has_blocked_user_with_id(user_id=target_user.pk):
        raise PermissionDenied(_('This account is blocked.'))

    if new_post_notifications_enabled:
        raise ValidationError(
            _('New post notifications are already enabled'),
        )


def check_can_disable_new_post_notifications_for_user(user, target_user):
    new_post_notifications_enabled = user.are_new_post_notifications_enabled_for_user(user=target_user)

    if target_user.has_blocked_user_with_id(user_id=user.pk) or user.has_blocked_user_with_id(user_id=target_user.pk):
        raise PermissionDenied(_('This account is blocked.'))

    if not new_post_notifications_enabled:
        raise ValidationError(
            _('You are not subscribed to new post notifications'),
        )
