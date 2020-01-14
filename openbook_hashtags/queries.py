from django.db.models import Q

from openbook_common.utils.model_loaders import get_moderated_object_model


def make_search_hashtag_query_for_user_with_id(search_query, user_id):
    query = Q(name__icontains=search_query)
    query.add(make_exclude_reported_and_approved_hashtags_query(), Q.AND)
    query.add(make_exclude_reported_hashtags_by_user_with_id_query(user_id=user_id), Q.AND)
    return query


def make_get_hashtag_with_name_query(name):
    return Q(name=name)


def make_exclude_reported_and_approved_hashtags_query():
    ModeratedObject = get_moderated_object_model()
    return ~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED)


def make_exclude_reported_hashtags_by_user_with_id_query(user_id):
    return ~Q(moderated_object__reports__reporter_id=user_id)


def make_get_hashtag_with_name_for_user_with_id_query(hashtag_name, user_id):
    query = make_get_hashtag_with_name_query(name=hashtag_name)
    query.add(make_exclude_reported_and_approved_hashtags_query(), Q.AND)
    query.add(make_exclude_reported_hashtags_by_user_with_id_query(user_id=user_id), Q.AND)
    return query
