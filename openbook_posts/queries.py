from django.db.models import Q

from openbook_common.utils.model_loaders import get_post_model, get_moderated_object_model, get_community_model, \
    get_circle_model


def make_only_posts_with_max_id(max_id):
    return Q(id__lt=max_id)


def make_only_posts_with_min_id(min_id):
    return Q(id__gt=min_id)


def make_only_posts_with_hashtag_with_id_query(hashtag_id):
    return Q(hashtags__id=hashtag_id)


def make_only_posts_for_creator_with_id_query(creator_id):
    return Q(creator_id=creator_id)


def make_only_posts_of_circles_part_for_user_with_id_query(user_id):
    return Q(circles__connections__target_user_id=user_id,
             circles__connections__target_connection__circles__isnull=False)


def make_only_published_posts_query():
    # Only retrieve published posts
    Post = get_post_model()
    return Q(status=Post.STATUS_PUBLISHED)


def make_exclude_soft_deleted_posts_query():
    return Q(is_deleted=False)


def make_exclude_reported_and_approved_posts_query():
    ModeratedObject = get_moderated_object_model()
    return ~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED)


def make_exclude_reported_posts_by_user_with_id_query(user_id):
    return ~Q(moderated_object__reports__reporter_id=user_id)


def make_exclude_community_posts_banned_from_for_user_with_id_query(user_id):
    return ~Q(community__banned_users__id=user_id)


def make_exclude_closed_posts_in_community_for_user_with_id_query(user_id):
    return make_exclude_closed_posts_query() | Q(creator_id=user_id)


def make_exclude_closed_posts_query():
    return Q(is_closed=False)


def make_exclude_blocked_community_posts_for_user_and_community_with_ids(user_id, community_id):
    # Don't retrieve posts of blocked users, except if they're staff members
    blocked_users_query = ~Q(Q(creator__blocked_by_users__blocker_id=user_id) | Q(
        creator__user_blocks__blocked_user_id=user_id))

    blocked_users_query_staff_members = Q(creator__communities_memberships__community_id=community_id)
    blocked_users_query_staff_members.add(Q(creator__communities_memberships__is_administrator=True) | Q(
        creator__communities_memberships__is_moderator=True), Q.AND)

    blocked_users_query.add(~blocked_users_query_staff_members, Q.AND)

    return blocked_users_query


def make_only_visible_community_posts_for_user_with_id_query(user_id):
    # Ensure public/private visibility is respected
    community_posts_visibility_query = Q(community__memberships__user__id=user_id)
    community_posts_visibility_query.add(make_only_public_community_posts_query(), Q.OR)

    return community_posts_visibility_query


def make_exclude_community_posts_query():
    return Q(community__isnull=True)


def make_exclude_blocked_posts_for_user_with_id_query(user_id):
    return ~Q(Q(creator__blocked_by_users__blocker_id=user_id) | Q(
        creator__user_blocks__blocked_user_id=user_id))


def make_only_public_community_posts_query():
    Community = get_community_model()
    return Q(community__type=Community.COMMUNITY_TYPE_PUBLIC, )


def make_only_world_circle_posts_query():
    Circle = get_circle_model()
    world_circle_id = Circle.get_world_circle().pk
    return Q(circles__id=world_circle_id)


def make_only_public_posts_query():
    return make_only_public_community_posts_query() | make_only_world_circle_posts_query()


def make_get_hashtag_posts_for_user_with_id_query(hashtag, user_id):
    # Retrieve posts with the given hashtag
    hashtag_posts_query = make_only_posts_with_hashtag_with_id_query(hashtag_id=hashtag.pk)

    # Only retrieve public posts
    hashtag_posts_query.add(make_only_public_posts_query(), Q.AND)

    # Dont retrieve soft deleted posts
    hashtag_posts_query.add(make_exclude_soft_deleted_posts_query(), Q.AND)

    # Dont retrieve posts from blocked people
    hashtag_posts_query.add(make_exclude_blocked_posts_for_user_with_id_query(user_id=user_id), Q.AND)

    # Only retrieve published posts
    hashtag_posts_query.add(make_only_published_posts_query(), Q.AND)

    # Don't retrieve items that have been reported and approved
    hashtag_posts_query.add(make_exclude_reported_and_approved_posts_query(), Q.AND)

    # Dont retrieve items we have reported
    hashtag_posts_query.add(make_exclude_reported_posts_by_user_with_id_query(user_id=user_id), Q.AND)

    # Dont retrieve posts from communities we're  banned from
    hashtag_posts_query.add(make_exclude_community_posts_banned_from_for_user_with_id_query(user_id=user_id), Q.AND)

    # Dont retrieve closed posts
    hashtag_posts_query.add(make_exclude_closed_posts_query(), Q.AND)

    return hashtag_posts_query


def make_circles_posts_query_for_user(user):
    target_user_circles_posts_query = make_only_posts_of_circles_part_for_user_with_id_query(
        user_id=user.pk) | make_only_world_circle_posts_query()

    return target_user_circles_posts_query


def make_community_posts_query_for_user(user):
    return make_only_visible_community_posts_for_user_with_id_query(user_id=user.pk)
