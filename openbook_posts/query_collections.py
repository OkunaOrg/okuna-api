from django.db.models import Q

from openbook_common.utils.model_loaders import get_post_model, get_moderated_object_model
from openbook_posts.queries import \
    make_community_posts_query_for_user, make_only_posts_with_max_id, \
    make_only_posts_with_min_id, make_circles_posts_query_for_user


def get_posts_for_user_collection(target_user, source_user, posts_only=None, posts_prefetch_related=None,
                                  max_id=None,
                                  min_id=None,
                                  include_community_posts=False):
    Post = get_post_model()

    posts_collection_manager = Post.objects

    if posts_prefetch_related:
        posts_collection_manager = posts_collection_manager.prefetch_related(*posts_prefetch_related)

    if posts_only:
        posts_collection_manager = posts_collection_manager.only(*posts_only)

    id_boundary_query = None

    if max_id:
        id_boundary_query = make_only_posts_with_max_id(max_id=max_id)
    elif min_id:
        id_boundary_query = make_only_posts_with_min_id(min_id=min_id)

    query = Q(
        # Created by the target user
        creator__username=target_user.username,
        # Not closed
        is_closed=False,
        # Not deleted
        is_deleted=False,
        # Published
        status=Post.STATUS_PUBLISHED,
    )

    posts_query = make_circles_posts_query_for_user(
        user=source_user
    )

    if include_community_posts:
        posts_query.add(make_community_posts_query_for_user(
            user=source_user
        ), Q.OR)

    query.add(posts_query, Q.AND)

    if id_boundary_query:
        query.add(id_boundary_query, Q.AND)

    ModeratedObject = get_moderated_object_model()

    posts_visibility_exclude_query = Q(
        # Excluded communities posts
        Q(community__profile_posts_community_exclusions__user=target_user.pk) |
        # Reported posts
        Q(moderated_object__reports__reporter_id=source_user.pk) |
        # Approved reported posts
        Q(moderated_object__status=ModeratedObject.STATUS_APPROVED) |
        # Posts of users we blocked or that have blocked us
        Q(creator__blocked_by_users__blocker_id=source_user.pk) | Q(
            creator__user_blocks__blocked_user_id=source_user.pk) |
        # Posts of communities banned from
        Q(community__banned_users__id=source_user.pk)
    )

    return posts_collection_manager.filter(query).exclude(posts_visibility_exclude_query).distinct()
