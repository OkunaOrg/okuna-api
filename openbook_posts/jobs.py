from django_rq import job
from datetime import datetime, timedelta
from openbook_posts.models import Post


@job
def flush_draft_posts():
    # Get all draft posts that haven't been modified for a day
    draft_posts = Post.objects.filter(status=Post.STATUS_DRAFT, modified__lt=datetime.now() - timedelta(days=1)).all()

    for draft_post in draft_posts.iterator():
        draft_post.delete()
