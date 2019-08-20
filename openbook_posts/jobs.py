from django_rq import job
from openbook_posts.models import Post
from django.utils import timezone

@job
def flush_draft_posts():
    # Get all draft posts that haven't been modified for a day
    draft_posts = Post.objects.filter(status=Post.STATUS_DRAFT,
                                      modified__lt=timezone.now() - timezone.timedelta(days=1)).all()

    flushed_posts = 0

    for draft_post in draft_posts.iterator():
        draft_post.delete()
        flushed_posts = flushed_posts + 1

    return 'Flushed %s posts' % str(flushed_posts)