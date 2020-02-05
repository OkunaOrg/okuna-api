from django.db.models import Q


def make_search_communities_query_for_user(query, user, excluded_from_profile_posts=True):
    """
    :param query:
    :param user:
    :param excluded_from_profile_posts: Whether to include the communities that were excluded from profile posts
    :return:
    """
    search_communities_query = make_search_communities_query(query=query)

    if not excluded_from_profile_posts:
        search_communities_query.add(~Q(profile_posts_community_exclusions__user_id=user), Q.AND)

    return search_communities_query


def make_search_communities_query(query):
    communities_query = Q(name__icontains=query)
    communities_query.add(Q(title__icontains=query), Q.OR)
    communities_query.add(Q(is_deleted=False), Q.AND)
    return communities_query
