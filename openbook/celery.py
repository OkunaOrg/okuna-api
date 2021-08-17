from datetime import timedelta
import os
from functools import wraps

from celery import Celery
from kombu import Queue, Exchange
from openbook.settings import CELERY_REDIS_BROKER_LOCATION, CELERY_REDIS_RESULT_BACKEND_LOCATION

CELERY_DEFAULT_PRIORITY_QUEUE = 'default_priority'
CELERY_LOW_PRIORITY_QUEUE = 'low_priority'
CELERY_HIGH_PRIORITY_QUEUE = 'high_priority'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openbook.settings')

celery = Celery(
    'openbook',
    broker=CELERY_REDIS_BROKER_LOCATION,
    backend=CELERY_REDIS_RESULT_BACKEND_LOCATION,
)

celery.conf['task_queues'] = (
    Queue(
        CELERY_DEFAULT_PRIORITY_QUEUE,
        Exchange(CELERY_DEFAULT_PRIORITY_QUEUE),
        routing_key=CELERY_DEFAULT_PRIORITY_QUEUE
    ),
    Queue(
        CELERY_LOW_PRIORITY_QUEUE,
        Exchange(CELERY_LOW_PRIORITY_QUEUE),
        routing_key=CELERY_LOW_PRIORITY_QUEUE
    ),
    Queue(
        CELERY_HIGH_PRIORITY_QUEUE,
        Exchange(CELERY_HIGH_PRIORITY_QUEUE),
        routing_key=CELERY_HIGH_PRIORITY_QUEUE
    ),
)

# TODO: make job scheduler dynamically configurable
celery.conf['beat_schedule'] = {
    'flush-draft-posts': {
        'task': 'openbook_posts.jobs.flush_draft_posts',
        'schedule': timedelta(hours=1),
    },

    'curate-top-posts': {
        'task': 'openbook_posts.jobs.curate_top_posts',
        'schedule': timedelta(minutes=15),
    },

    'clean-top-posts': {
        'task': 'openbook_posts.jobs.clean_top_posts',
        'schedule': timedelta(hours=12),
    },

    'curate-trending-posts': {
        'task': 'openbook_posts.jobs.curate_trending_posts',
        'schedule': timedelta(minutes=5),
    },

    'clean-trending-posts': {
        'task': 'openbook_posts.jobs.clean_trending_posts',
        'schedule': timedelta(hours=1),
    },
}

def celery_use_eager(func):
    """
    Decorator that makes sure that the tasks invoked by a function are executed
    in eager mode. Useful for unit testing.
    """
    @wraps(func)
    def inner(*args, **kwargs):
        celery.conf.update(task_always_eager=True)
        func(*args, **kwargs)
        celery.conf.update(task_always_eager=False)
    return inner
