from django.db.models import Q
from django_rq import job
from django.conf import settings
from django.core.cache import caches
from django.utils import timezone

from openbook_common.utils.model_loaders import get_trending_community_model, get_community_model, \
    get_moderated_object_model
import logging

logger = logging.getLogger(__name__)


@job('low')
def curate_trending_communities():
    """
    Curates trending communities. Repeating job.
    """
    logger.info('Curating trending communities')
    TrendingCommunity = get_trending_community_model()
    Community = get_community_model()
    ModeratedObject = get_moderated_object_model()
    # redis_cache = caches['community-activity-scores']
    # all_keys = redis_cache.iter_keys('community_*')

    # community_scores_dict = {}

    # for key in all_keys:
    #     community_id = key.split('_')[1]
    #     if community_id not in community_scores_dict.keys():
    #         community_keys_dict = redis_cache.get_many(redis_cache.keys("community_{0}_*".format(community_id)))
    #         community_activity_score = sum(community_keys_dict.values())
    #         community_scores_dict[community_id] = community_activity_score

    # for item in sorted(community_scores_dict.items(), key=lambda kv: (kv[1], kv[0])):
    #     TrendingCommunity.objects.create(community_id=item[0])

    TrendingCommunity.objects.all().delete()

    communities_only = ('id', 'activity_score', 'type')
    trending_communities_query = Q(type=Community.COMMUNITY_TYPE_PUBLIC)
    trending_communities_query.add(Q(activity_score__gte=settings.MIN_ACTIVITY_SCORE_FOR_COMMUNITY_TRENDING), Q.AND)
    trending_communities_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

    top_trending_communities = Community.objects. \
    prefetch_related('moderated_object'). \
    only(*communities_only). \
    filter(trending_communities_query). \
    order_by('-activity_score')[:100]

    trending_communities_objects = []

    for community in top_trending_communities.iterator():
        if TrendingCommunity.objects.filter(community=community).exists():
            TrendingCommunity.objects.filter(community=community).delete()

        trending_community = TrendingCommunity(community=community, created=timezone.now())
        trending_communities_objects.insert(0, trending_community)

    TrendingCommunity.objects.bulk_create(trending_communities_objects)

    logger.info('Curated {0} trending communities'.format(len(trending_communities_objects)))
