from django_rq import job
from django.core.cache import caches

from openbook_common.utils.model_loaders import get_trending_community_model
import logging

logger = logging.getLogger(__name__)


@job('low')
def curate_trending_communities():
    """
    Curates trending communities. Repeating job.
    """
    logger.info('Curating trending communities')
    TrendingCommunity = get_trending_community_model()
    redis_cache = caches['community-activity-scores']
    all_keys = redis_cache.iter_keys('community_*')

    community_scores_dict = {}

    for key in all_keys:
        community_id = key.split('_')[1]
        if community_id not in community_scores_dict.keys():
            community_keys_dict = redis_cache.get_many(redis_cache.keys("community_{0}_*".format(community_id)))
            community_activity_score = sum(community_keys_dict.values())
            community_scores_dict[community_id] = community_activity_score

    TrendingCommunity.objects.all().delete()

    for item in sorted(community_scores_dict.items(), key=lambda kv: (kv[1], kv[0])):
        TrendingCommunity.objects.create(community_id=item[0])

    logger.info('Curated {0} trending communities'.format(len(community_scores_dict)))
