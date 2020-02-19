from django.utils import timezone
from django_rq import job, get_scheduler, get_queue
from video_encoding import tasks
from datetime import timedelta, datetime
from django.db.models import Q, Count, F
from django.conf import settings
from cursor_pagination import CursorPaginator

from openbook_common.utils.model_loaders import get_post_model, get_post_media_model, get_community_model, \
    get_top_post_model, get_post_comment_model, get_moderated_object_model, get_trending_post_model, \
    get_post_reaction_model
import logging

logger = logging.getLogger(__name__)


@job('low')
def flush_draft_posts():
    """
    This job should be scheduled to get all pending draft posts for a day and remove them
    """
    Post = get_post_model()

    draft_posts = Post.objects.filter(status=Post.STATUS_DRAFT,
                                      modified__lt=timezone.now() - timezone.timedelta(days=1)).all()

    flushed_posts = 0

    for draft_post in draft_posts.iterator():
        draft_post.delete()
        flushed_posts = flushed_posts + 1

    return 'Flushed %s posts' % str(flushed_posts)


@job('high')
def process_post_media(post_id):
    """
    This job is called to process post media and mark it as published
    """
    Post = get_post_model()
    PostMedia = get_post_media_model()
    post = Post.objects.get(pk=post_id)
    logger.info('Processing media of post with id: %d' % post_id)

    post_media_videos = post.media.filter(type=PostMedia.MEDIA_TYPE_VIDEO)

    for post_media_video in post_media_videos.iterator():
        post_video = post_media_video.content_object
        tasks.convert_video(post_video.file)

    # This updates the status and created attributes
    post._publish()
    logger.info('Processed media of post with id: %d' % post_id)


def _reduce_atomic_community_activity_score(community_id):
    Community = get_community_model()
    community = Community.objects.get(id=community_id)
    if community:
        community.activity_score = F('activity_score') - settings.ACTIVITY_ATOMIC_WEIGHT
        community.save()


def _process_community_activity_score_reaction_added(community, post_reaction_id):
    default_scheduler = get_scheduler('default')
    expire_datetime = datetime.utcnow() + timedelta(hours=settings.ACTIVITY_SCORE_EXPIRY_IN_HOURS)
    community.activity_score = F('activity_score') + settings.ACTIVITY_UNIQUE_REACTION_WEIGHT
    community.save()

    # schedule reduction of activity scores
    default_scheduler.enqueue_at(expire_datetime, _reduce_atomic_community_activity_score, community.pk,
                                 job_id='expire_community_{0}_rid_{1}_unique_reaction'.format(
                                     community.pk, post_reaction_id))


def _process_community_activity_score_reaction_deleted(community, post_reaction_id):
    default_scheduler = get_scheduler('default')
    reaction_job_id = 'expire_community_{0}_rid_{1}_unique_reaction'.format(community.pk, post_reaction_id)

    if reaction_job_id in default_scheduler:
        default_scheduler.cancel(reaction_job_id)
        community.activity_score = F('activity_score') - settings.ACTIVITY_UNIQUE_REACTION_WEIGHT
        community.save()


def process_activity_score_post_reaction(post_id, post_reaction_id):
    """
    This job is called to process activity score on a post after add/remove reaction
    """
    remove_reaction_job_id = 'process_remove_unique_reaction_pid_{0}_rid_{1}'.format(post_id, post_reaction_id)
    default_queue = get_queue('default')
    remove_job = default_queue.fetch_job(remove_reaction_job_id)

    if remove_reaction_job_id in default_queue.job_ids:
        # remove job is also queued, jobs cancel each other, return
        remove_job.cancel()
        return

    Post = get_post_model()
    PostReaction = get_post_reaction_model()
    Community = get_community_model()
    if not Post.objects.filter(pk=post_id).exists():
        # if post was deleted, return
        return

    post = Post.objects.get(pk=post_id)
    # redis_cache = caches['community-activity-scores']
    logger.info('Processing activity score for reaction of post with id: %d' % post_id)

    if post.community is not None and post.community.type is Community.COMMUNITY_TYPE_PUBLIC:
        # community_reaction_key = 'expire_community_{0}_rid_{1}'.format(post.community.pk, post_reaction_id)
        # current_activity_score = redis_cache.get(community_reaction_key, default=0)

        if not PostReaction.objects.filter(pk=post_reaction_id).exists():
            # reaction was deleted
            post.activity_score = F('activity_score') - settings.ACTIVITY_UNIQUE_REACTION_WEIGHT
            _process_community_activity_score_reaction_deleted(post.community, post_reaction_id)
            # current_activity_score -= settings.ACTIVITY_UNIQUE_REACTION_WEIGHT
        else:
            # reaction was added
            post.activity_score = F('activity_score') + settings.ACTIVITY_UNIQUE_REACTION_WEIGHT
            _process_community_activity_score_reaction_added(post.community, post_reaction_id)
            # current_activity_score += settings.ACTIVITY_UNIQUE_REACTION_WEIGHT

        # if current_activity_score <= 0:
        #     redis_cache.expire(community_reaction_key, timeout=0)
        # else:
        #     redis_cache.set(community_reaction_key, current_activity_score,  timeout=3600*12)

    elif post.community is None and not PostReaction.objects.filter(pk=post_reaction_id).exists():
        # reaction was deleted
            post.activity_score = F('activity_score') - settings.ACTIVITY_UNIQUE_REACTION_WEIGHT
    else:
        # reaction was added
        post.activity_score = F('activity_score') + settings.ACTIVITY_UNIQUE_REACTION_WEIGHT

    post.save()
    logger.info('Processed activity score for reaction of post with id: %d' % post_id)


def _process_post_activity_score_comment_deleted(post, commenter_comments_count):
    if commenter_comments_count > 0:
        # there are still other comments by this user
        post.activity_score = F('activity_score') - settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
    else:
        # no more comments anymore by this user, subtract the unique comment weight too
        post.activity_score = F('activity_score') - \
                              settings.ACTIVITY_UNIQUE_COMMENT_WEIGHT - \
                              settings.ACTIVITY_COUNT_COMMENTS_WEIGHT


def _process_post_activity_score_comment_added(post, commenter_comments_count):
    if commenter_comments_count > 1:
        post.activity_score = F('activity_score') + settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
    elif commenter_comments_count == 1:
        post.activity_score = F('activity_score') + \
                              settings.ACTIVITY_UNIQUE_COMMENT_WEIGHT + \
                              settings.ACTIVITY_COUNT_COMMENTS_WEIGHT


def _process_community_activity_score_comment_deleted(community,
                                                      post_id,
                                                      post_comment_id,
                                                      post_commenter_id,
                                                      commenter_comments_count):

    default_scheduler = get_scheduler('default')
    job_id = 'expire_community_{0}_pid_{1}_uid_{2}_cid_{3}'.format(community.pk, post_id,
                                                                   post_commenter_id, post_comment_id)
    unique_comment_job_id = 'expire_community_{0}_pid_{1}_uid_{2}_unique_comment'.format(community.pk,
                                                                                         post_id, post_commenter_id)

    if job_id in default_scheduler:
        # there are still other comments by this user
        default_scheduler.cancel(job_id)
        community.activity_score = F('activity_score') - settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
        community.save()

    if commenter_comments_count == 0 and unique_comment_job_id in default_scheduler:
        # no more comments anymore by this user, subtract the unique comment weight too
        community.activity_score = F('activity_score') - settings.ACTIVITY_UNIQUE_COMMENT_WEIGHT
        default_scheduler.cancel(unique_comment_job_id)
        community.save()


def _process_community_activity_score_comment_added(community,
                                                    post_id,
                                                    post_comment_id,
                                                    post_commenter_id):
    default_scheduler = get_scheduler('default')
    unique_comment_job_id = 'expire_community_{0}_pid_{1}_uid_{2}_unique_comment'.format(community.pk,
                                                                                         post_id, post_commenter_id)
    expire_datetime = timezone.now() + timedelta(hours=settings.ACTIVITY_SCORE_EXPIRY_IN_HOURS)

    if unique_comment_job_id in default_scheduler:
        community.activity_score = F('activity_score') + settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
    else:
        community.activity_score = F('activity_score') + \
                                   settings.ACTIVITY_UNIQUE_COMMENT_WEIGHT + \
                                   settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
    community.save()
    if unique_comment_job_id in default_scheduler:
        default_scheduler.cancel(unique_comment_job_id)

    # schedule reduction of activity scores
    default_scheduler.enqueue_at(expire_datetime, _reduce_atomic_community_activity_score, community.pk,
                                 job_id=unique_comment_job_id)
    default_scheduler.enqueue_at(expire_datetime, _reduce_atomic_community_activity_score, community.pk,
                                 job_id='expire_community_{0}_pid_{1}_uid_{2}_cid_{3}'.format(
                                     community.pk, post_id, post_commenter_id, post_comment_id)
                                 )

# def _process_redis_activity_score_comment_deleted(commenter_comments_count,
#                                                   current_activity_score=None,
#                                                   redis_cache=None,
#                                                   community_comment_key=None):
#     if commenter_comments_count > 0:
#         # there are still other comments by this user
#         current_activity_score -= settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
#     else:
#         # no more comments anymore by this user, subtract the unique comment weight too
#         current_activity_score = current_activity_score - \
#                              settings.ACTIVITY_COUNT_COMMENTS_WEIGHT - \
#                              settings.ACTIVITY_UNIQUE_COMMENT_WEIGHT
#
#     if current_activity_score <= 0:
#         # expire immediately if score less than 0
#         redis_cache.expire(community_comment_key, timeout=0)
#     else:
#         redis_cache.set(community_comment_key, current_activity_score, timeout=3600*12)

# def _process_redis_activity_score_comment_added(commenter_comments_count,
#                                                 current_activity_score=None,
#                                                 redis_cache=None,
#                                                 community_comment_key=None):
#     Post = get_post_model()
#     if commenter_comments_count > 1:
#         current_activity_score += settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
#     elif commenter_comments_count == 1:
#         current_activity_score = current_activity_score + \
#                           settings.ACTIVITY_UNIQUE_COMMENT_WEIGHT + \
#                           settings.ACTIVITY_COUNT_COMMENTS_WEIGHT
#
#     redis_cache.set(community_comment_key, current_activity_score, timeout=3600*12)


def process_activity_score_post_comment(post_id, post_comment_id, post_commenter_id):
    """
    This job is called to process activity score on a post after add/remove comment
    """
    delete_comment_job_id = 'process_delete_comment_pid_{0}_cid_{1}'.format(post_id, post_comment_id)
    default_queue = get_queue('default')
    delete_job = default_queue.fetch_job(delete_comment_job_id)

    if delete_job is not None and delete_job.is_queued:
        # remove job is also queued, jobs cancel each other, return
        delete_job.cancel()
        return

    Post = get_post_model()
    PostComment = get_post_comment_model()
    Community = get_community_model()
    if not Post.objects.filter(pk=post_id).exists():
        # if post was deleted, return
        return

    post = Post.objects.get(pk=post_id)
    # redis_cache = caches['community-activity-scores']
    logger.info('Processing activity score for comment of post with id: %d' % post_id)

    commenter_comments_count = PostComment.objects.filter(post_id=post_id,
                                                          is_deleted=False,
                                                          commenter_id=post_commenter_id).count()

    if post.community is not None and post.community.type is Community.COMMUNITY_TYPE_PUBLIC:
        # community_comment_key = 'expire_community_{0}_uid_{1}_cid_{2}'.format(post.community.pk,
        #                                                                post_commenter_id,
        #                                                                post_comment_id)
        # current_activity_score = redis_cache.get(community_comment_key, default=0)

        if not PostComment.objects.filter(pk=post_comment_id).exists():
            # comment was deleted

            _process_post_activity_score_comment_deleted(post, commenter_comments_count)
            _process_community_activity_score_comment_deleted(post.community,
                                                              post_id,
                                                              post_comment_id,
                                                              post_commenter_id,
                                                              commenter_comments_count)
            # _process_redis_activity_score_comment_deleted(commenter_comments_count,
            #                                               redis_cache=redis_cache,
            #                                               current_activity_score=current_activity_score,
            #                                               community_comment_key=community_comment_key)
        else:
            # comment was added
            _process_post_activity_score_comment_added(post, commenter_comments_count)
            _process_community_activity_score_comment_added(post.community,
                                                            post_id,
                                                            post_comment_id,
                                                            post_commenter_id)
            # _process_redis_activity_score_comment_added(commenter_comments_count,
            #                                             redis_cache=redis_cache,
            #                                             current_activity_score=current_activity_score,
            #                                             community_comment_key=community_comment_key)
    else:
        if not PostComment.objects.filter(pk=post_comment_id).exists():
            # comment was deleted
            _process_post_activity_score_comment_deleted(post, commenter_comments_count)
        else:
            # comment was added
            _process_post_activity_score_comment_added(post, commenter_comments_count)

    post.save()
    logger.info('Processed activity score for comment of post with id: %d' % post_id)


def _process_community_activity_score_post_added(post, total_posts_by_creator):
    default_scheduler = get_scheduler('default')
    expire_datetime = timezone.now() + timedelta(hours=settings.ACTIVITY_SCORE_EXPIRY_IN_HOURS)
    unique_post_job_id = 'expire_community_{0}_uid_{1}_unique_post'.format(
        post.community.pk,
        post.creator.pk)

    if unique_post_job_id in default_scheduler:
        post.community.activity_score = F('activity_score') + settings.ACTIVITY_COUNT_POSTS_WEIGHT
    else:
        post.community.activity_score = F('activity_score') + \
                                    settings.ACTIVITY_UNIQUE_POST_WEIGHT + \
                                    settings.ACTIVITY_COUNT_POSTS_WEIGHT

    post.community.save()
    if unique_post_job_id in default_scheduler:
        default_scheduler.cancel(unique_post_job_id)

    # schedule reduction of activity scores
    default_scheduler.enqueue_at(expire_datetime, _reduce_atomic_community_activity_score, post.community.pk,
                                 job_id=unique_post_job_id)
    default_scheduler.enqueue_at(expire_datetime, _reduce_atomic_community_activity_score, post.community.pk,
                                 job_id='expire_community_{0}_pid_{1}'.format(
                                     post.community.pk, post.pk)
                                 )


def _process_community_activity_score_post_deleted(post_id, post_creator_id,
                                                   post_community_id, total_posts_by_creator):

    default_scheduler = get_scheduler('default')
    job_id = 'expire_community_{0}_pid_{1}'.format(post_community_id, post_id)
    unique_post_job_id = 'expire_community_{0}_uid_{1}_unique_post'.format(post_community_id,
                                                                           post_creator_id)

    Community = get_community_model()
    community = Community.objects.get(id=post_community_id)
    if job_id in default_scheduler:
        default_scheduler.cancel(job_id)
        community.activity_score = F('activity_score') - settings.ACTIVITY_COUNT_POSTS_WEIGHT
        community.save()

    if total_posts_by_creator == 0 and unique_post_job_id in default_scheduler:
        community.activity_score = F('activity_score') - settings.ACTIVITY_UNIQUE_POST_WEIGHT
        default_scheduler.cancel(unique_post_job_id)
        community.save()


def process_community_activity_score_post(post_id, post_creator_id, post_community_id):
    """
    This job is called to process activity score on a community after add/remove post
    """
    logger.info('Processing community activity score for create/delete post with id: %d' % post_id)

    delete_post_job_id = 'process_delete_community_post_community_{0}_pid_{1}_uid_{2}'.format(post_community_id,
                                                                                              post_id,
                                                                                              post_creator_id)
    default_queue = get_queue('default')
    delete_post_job = default_queue.fetch_job(delete_post_job_id)

    if delete_post_job is not None and delete_post_job.is_queued:
        # delete post job is also queued, jobs cancel each other, return
        delete_post_job.cancel()
        return

    Post = get_post_model()
    Community = get_community_model()
    if not Community.objects.filter(id=post_community_id).exists():
        # if community was deleted, return
        return

    creator_posts_query = Q(created__gte=timezone.now() - timedelta(hours=settings.ACTIVITY_SCORE_EXPIRY_IN_HOURS))
    creator_posts_query.add(Q(creator_id=post_creator_id, community_id=post_community_id), Q.AND)

    total_posts_by_creator = Post.objects.filter(creator_posts_query).count()

    if Post.objects.filter(pk=post_id).exists():
        # post was added
        post = Post.objects.get(pk=post_id)
        _process_community_activity_score_post_added(post, total_posts_by_creator)
    else:
        # post was removed
        _process_community_activity_score_post_deleted(post_id,
                                                       post_creator_id,
                                                       post_community_id,
                                                       total_posts_by_creator)
    logger.info('Processed community activity score for create/delete post with id: %d' % post_id)


@job('low')
def curate_top_posts():
    """
    Curates the top posts.
    This job should be scheduled to be run every n hours.
    """
    Post = get_post_model()
    Community = get_community_model()
    PostComment = get_post_comment_model()
    ModeratedObject = get_moderated_object_model()
    TopPost = get_top_post_model()
    logger.info('Processing top posts at %s...' % timezone.now())

    top_posts_community_query = Q(top_post__isnull=True)
    top_posts_community_query.add(Q(community__isnull=False, community__type=Community.COMMUNITY_TYPE_PUBLIC), Q.AND)
    top_posts_community_query.add(Q(is_closed=False, is_deleted=False, status=Post.STATUS_PUBLISHED), Q.AND)
    top_posts_community_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

    top_posts_criteria_query = Q(total_comments_count__gte=settings.MIN_UNIQUE_TOP_POST_COMMENTS_COUNT) | \
                               Q(reactions_count__gte=settings.MIN_UNIQUE_TOP_POST_REACTIONS_COUNT)

    posts_select_related = 'community'
    posts_prefetch_related = ('comments__commenter', 'reactions__reactor')
    posts_only = ('id', 'status', 'is_deleted', 'is_closed', 'community__type')

    posts = Post.objects. \
        select_related(posts_select_related). \
        prefetch_related(*posts_prefetch_related). \
        only(*posts_only). \
        filter(top_posts_community_query). \
        annotate(total_comments_count=Count('comments__commenter_id'),
                 reactions_count=Count('reactions__reactor_id')). \
        filter(top_posts_criteria_query)

    top_posts_objects = []
    total_checked_posts = 0
    total_curated_posts = 0

    for post in _chunked_queryset_iterator(posts, 1000):
        total_checked_posts = total_checked_posts + 1
        if not post.reactions_count >= settings.MIN_UNIQUE_TOP_POST_REACTIONS_COUNT:
            unique_comments_count = PostComment.objects.filter(post=post). \
                values('commenter_id'). \
                annotate(user_comments_count=Count('commenter_id')).count()

            if unique_comments_count >= settings.MIN_UNIQUE_TOP_POST_COMMENTS_COUNT:
                top_post = _add_post_to_top_post(post=post)
                if top_post is not None:
                    top_posts_objects.append(top_post)
        else:
            top_post = _add_post_to_top_post(post=post)
            if top_post is not None:
                top_posts_objects.append(top_post)

        if len(top_posts_objects) > 1000:
            TopPost.objects.bulk_create(top_posts_objects)
            total_curated_posts += len(top_posts_objects)
            top_posts_objects = []

    if len(top_posts_objects) > 0:
        total_curated_posts += len(top_posts_objects)
        TopPost.objects.bulk_create(top_posts_objects)

    return 'Checked: %d. Curated: %d' % (total_checked_posts, total_curated_posts)


@job('low')
def clean_top_posts():
    """
    Cleans up top posts, that no longer meet the criteria.
    """
    Post = get_post_model()
    Community = get_community_model()
    TopPost = get_top_post_model()
    PostComment = get_post_comment_model()
    ModeratedObject = get_moderated_object_model()

    # if any of these is true, we will remove the top post
    top_posts_community_query = Q(post__community__type=Community.COMMUNITY_TYPE_PRIVATE)
    top_posts_community_query.add(Q(post__is_closed=True), Q.OR)
    top_posts_community_query.add(Q(post__is_deleted=True), Q.OR)
    top_posts_community_query.add(Q(post__status=Post.STATUS_DRAFT), Q.OR)
    top_posts_community_query.add(Q(post__status=Post.STATUS_PROCESSING), Q.OR)
    top_posts_community_query.add(Q(post__moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.OR)

    # counts less than minimum
    top_posts_criteria_query = Q(total_comments_count__lt=settings.MIN_UNIQUE_TOP_POST_COMMENTS_COUNT) & \
                               Q(reactions_count__lt=settings.MIN_UNIQUE_TOP_POST_REACTIONS_COUNT)

    posts_select_related = 'post__community'
    posts_prefetch_related = ('post__comments__commenter', 'post__reactions__reactor')
    posts_only = ('post__id', 'post__status', 'post__is_deleted', 'post__is_closed', 'post__community__type')

    direct_removable_top_posts = TopPost.objects.select_related(posts_select_related). \
        prefetch_related(*posts_prefetch_related). \
        only(*posts_only). \
        filter(top_posts_community_query). \
        annotate(total_comments_count=Count('post__comments__commenter_id'),
                 reactions_count=Count('post__reactions__reactor_id')). \
        filter(top_posts_criteria_query)

    # bulk delete all that definitely dont meet the criteria anymore
    direct_removable_top_posts.delete()

    # Now we need to only check the ones where the unique comments count might have dropped,
    # while all other criteria is fine

    top_posts_community_query = Q(post__community__isnull=False, post__community__type=Community.COMMUNITY_TYPE_PUBLIC)
    top_posts_community_query.add(Q(post__is_closed=False, post__is_deleted=False, post__status=Post.STATUS_PUBLISHED),
                                  Q.AND)
    top_posts_community_query.add(~Q(post__moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

    top_posts_criteria_query = Q(total_comments_count__gte=settings.MIN_UNIQUE_TOP_POST_COMMENTS_COUNT) | \
                               Q(reactions_count__gte=settings.MIN_UNIQUE_TOP_POST_REACTIONS_COUNT)

    top_posts = TopPost.objects.select_related(posts_select_related). \
        prefetch_related(*posts_prefetch_related). \
        only(*posts_only). \
        filter(top_posts_community_query). \
        annotate(total_comments_count=Count('post__comments__commenter_id'),
                 reactions_count=Count('post__reactions__reactor_id')). \
        filter(top_posts_criteria_query)

    delete_ids = []

    for top_post in _chunked_queryset_iterator(top_posts, 1000):
        if not top_post.reactions_count >= settings.MIN_UNIQUE_TOP_POST_REACTIONS_COUNT:
            unique_comments_count = PostComment.objects.filter(post=top_post.post). \
                values('commenter_id'). \
                annotate(user_comments_count=Count('commenter_id')).count()

            if unique_comments_count < settings.MIN_UNIQUE_TOP_POST_COMMENTS_COUNT:
                delete_ids.append(top_post.pk)

    # bulk delete ids
    TopPost.objects.filter(id__in=delete_ids).delete()


def _add_post_to_top_post(post):
    TopPost = get_top_post_model()
    if not TopPost.objects.filter(post=post).exists():
        return TopPost(post=post, created=timezone.now())
    return None


@job('low')
def curate_trending_posts():
    """
    Curates the trending posts.
    This job should be scheduled to be run every n hours.
    """
    Post = get_post_model()
    Community = get_community_model()
    ModeratedObject = get_moderated_object_model()
    TrendingPost = get_trending_post_model()
    logger.info('Processing trending posts at %s...' % timezone.now())

    trending_posts_query = Q(created__gte=timezone.now() - timedelta(
        hours=12))

    trending_posts_community_query = Q(community__isnull=False, community__type=Community.COMMUNITY_TYPE_PUBLIC,
                                       status=Post.STATUS_PUBLISHED,
                                       is_closed=False, is_deleted=False)
    trending_posts_community_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

    trending_posts_query.add(trending_posts_community_query, Q.AND)

    trending_posts_criteria_query = Q(activity_score__gte=settings.MIN_ACTIVITY_SCORE_FOR_TRENDING)

    trending_posts_query.add(trending_posts_criteria_query, Q.AND)

    posts_select_related = 'community'
    posts_only = ('id', 'status', 'activity_score', 'is_deleted', 'is_closed', 'community__type')

    posts = Post.objects. \
        select_related(posts_select_related). \
        only(*posts_only). \
        filter(trending_posts_query). \
        order_by('-activity_score', '-created')[:30]

    trending_posts_objects = []

    for post in posts.iterator():
        if TrendingPost.objects.filter(post=post).exists():
            TrendingPost.objects.filter(post=post).delete()

        trending_post = TrendingPost(post=post, created=timezone.now())
        trending_posts_objects.insert(0, trending_post)

    TrendingPost.objects.bulk_create(trending_posts_objects)

    return 'Curated: %d posts' % posts.count()


@job('low')
def bootstrap_trending_posts():
    """
    Bootstraps the trending posts.
    This job should be run exactly ONCE
    """
    Post = get_post_model()
    Community = get_community_model()
    ModeratedObject = get_moderated_object_model()
    TrendingPost = get_trending_post_model()
    logger.info('Processing trending posts at %s...' % timezone.now())

    trending_posts_community_query = Q(community__isnull=False, community__type=Community.COMMUNITY_TYPE_PUBLIC,
                                       status=Post.STATUS_PUBLISHED,
                                       is_closed=False, is_deleted=False)

    trending_posts_community_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

    trending_posts_criteria_query = Q(activity_score__gte=settings.MIN_ACTIVITY_SCORE_FOR_TRENDING)

    trending_posts_community_query.add(trending_posts_criteria_query, Q.AND)

    posts_select_related = 'community'
    posts_only = ('id', 'status', 'activity_score', 'is_deleted', 'is_closed', 'community__type')

    posts = Post.objects. \
        select_related(posts_select_related). \
        only(*posts_only). \
        filter(trending_posts_community_query). \
        order_by('-created')

    trending_posts_objects = []
    total_curated_posts = 0
    total_checked_posts = 0

    for post in _chunked_queryset_iterator(posts, 1000):
        total_checked_posts += 1
        trending_post = TrendingPost(post=post, created=timezone.now())
        trending_posts_objects.append(trending_post)

        if len(trending_posts_objects) > 1000:
            TrendingPost.objects.bulk_create(trending_posts_objects)
            total_curated_posts += len(trending_posts_objects)
            trending_posts_objects = []

    if len(trending_posts_objects) > 0:
        total_curated_posts += len(trending_posts_objects)
        TrendingPost.objects.bulk_create(trending_posts_objects)

    return 'Checked: %d. Curated: %d' % (total_checked_posts, total_curated_posts)


@job('low')
def clean_trending_posts():
    """
    Cleans trending posts.
    This job should be scheduled to be run every n hours.
    """
    Post = get_post_model()
    Community = get_community_model()
    TrendingPost = get_trending_post_model()
    ModeratedObject = get_moderated_object_model()

    # if any of these is true, we will remove the trending post
    trending_posts_community_query = Q(post__community__type=Community.COMMUNITY_TYPE_PRIVATE)
    trending_posts_community_query.add(Q(post__is_closed=True), Q.OR)
    trending_posts_community_query.add(Q(post__is_deleted=True), Q.OR)
    trending_posts_community_query.add(Q(post__status=Post.STATUS_DRAFT), Q.OR)
    trending_posts_community_query.add(Q(post__status=Post.STATUS_PROCESSING), Q.OR)
    trending_posts_community_query.add(Q(post__moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.OR)
    trending_posts_community_query.add(Q(post__activity_score__lt=settings.MIN_ACTIVITY_SCORE_FOR_TRENDING), Q.OR)

    posts_select_related = 'post__community'
    posts_only = ('post__id', 'post__status', 'post__activity_score', 'post__is_deleted', 'post__is_closed',
                  'post__community__type')

    removable_trending_posts = TrendingPost.objects.select_related(posts_select_related). \
        only(*posts_only). \
        filter(trending_posts_community_query)

    direct_removable_delete_ids = [trending_post.pk for trending_post in removable_trending_posts]

    # delete posts
    TrendingPost.objects.filter(id__in=direct_removable_delete_ids).delete()


def _chunked_queryset_iterator(queryset, size, *, ordering=('id',)):
    """
    Split a queryset into chunks.
    This can be used instead of `queryset.iterator()`,
    so `.prefetch_related()` also works
    Note::
    The ordering must uniquely identify the object,
    and be in the same order (ASC/DESC). See https://github.com/photocrowd/django-cursor-pagination
    """
    pager = CursorPaginator(queryset, ordering)
    after = None
    while True:
        page = pager.page(after=after, first=size)
        if page:
            yield from page.items
        else:
            return
        if not page.has_next:
            break
        # take last item, next page starts after this.
        after = pager.cursor(instance=page[-1])
