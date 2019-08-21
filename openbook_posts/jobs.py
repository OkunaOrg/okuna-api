from django.utils import timezone
from django_rq import job
from video_encoding import tasks

from openbook_common.utils.model_loaders import get_post_model, get_post_media_model


@job
def flush_draft_posts():
    """
    This job should be scheduled
    """
    # Get all draft posts that haven't been modified for a day
    Post = get_post_model()

    draft_posts = Post.objects.filter(status=Post.STATUS_DRAFT,
                                      modified__lt=timezone.now() - timezone.timedelta(days=1)).all()

    flushed_posts = 0

    for draft_post in draft_posts.iterator():
        draft_post.delete()
        flushed_posts = flushed_posts + 1

    return 'Flushed %s posts' % str(flushed_posts)


@job
def process_post_media(post_id):
    Post = get_post_model()
    PostMedia = get_post_media_model()
    post = Post.objects.get(pk=post_id)

    post_media_videos = post.media.filter(type=PostMedia.MEDIA_TYPE_VIDEO)

    for post_media_video in post_media_videos.iterator():
        post_video = post_media_video.content_object
        tasks.convert_video(post_video.file)

    # This updates the status and created attributes
    post.__publish()
