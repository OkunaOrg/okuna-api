from django.db.models import Q

from openbook_common.utils.model_loaders import get_post_model
from openbook_posts.queries import \
    make_community_posts_query_for_target_user_and_source_user, make_only_posts_with_max_id, \
    make_only_posts_with_min_id, make_circles_posts_query_for_target_user_and_source_user


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

    circles_posts_query = make_circles_posts_query_for_target_user_and_source_user(
        target_user=target_user,
        source_user=source_user
    )

    if id_boundary_query:
        circles_posts_query.add(id_boundary_query, Q.AND)

    circles_posts_collection = posts_collection_manager.filter(circles_posts_query)

    if not include_community_posts:
        return circles_posts_collection

    community_posts_query = make_community_posts_query_for_target_user_and_source_user(
        target_user=target_user,
        source_user=source_user
    )

    if id_boundary_query:
        community_posts_query.add(id_boundary_query, Q.AND)

    community_posts_collection = posts_collection_manager.filter(community_posts_query)

    return community_posts_collection.union(circles_posts_collection)
