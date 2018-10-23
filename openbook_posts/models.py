# Create your models here.
from django.apps import apps
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Create your views here.
from openbook_auth.models import User

# #FFFFFF
from openbook_common.models import Emoji


def get_circle_model():
    return apps.get_model('openbook_circles.Circle')


class Post(models.Model):
    text = models.CharField(_('text'), max_length=560, blank=False, null=False)
    created = models.DateTimeField(editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')

    @classmethod
    def create_post(cls, text, creator, circles_ids=None, image=None):
        if circles_ids is None or len(circles_ids) == 0:
            circles_ids = [creator.world_circle_id]

        post = Post.objects.create(text=text, creator=creator)

        if image:
            PostImage.objects.create(image=image, post_id=post.pk)

        post.circles.add(*circles_ids)

        return post

    @classmethod
    def get_posts_for_user(cls, user):
        posts_queryset = user.posts.all()

        connections = user.connections.all()
        for connection in connections:
            target_connection = connection.target_connection
            target_user = target_connection.user

            # Add connection connections circle posts
            target_user_connections_circle = target_user.connections_circle
            posts_queryset = posts_queryset | target_user_connections_circle.posts.all()

            # Add connection circle posts
            target_connection_circle = target_connection.circle
            if target_connection_circle:
                posts_queryset = posts_queryset | target_connection_circle.posts.all()

        follows = user.follows.all()
        for follow in follows:
            followed_user = follow.followed_user
            posts_queryset = posts_queryset | followed_user.world_circle.posts.all()

        return posts_queryset

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Post, self).save(*args, **kwargs)


class PostImage(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='image')
    image = models.ImageField(_('image'), blank=False, null=False)


class PostComment(models.Model):
    created = models.DateTimeField(editable=False)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts_comments')
    text = models.CharField(_('text'), max_length=280, blank=False, null=False)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostComment, self).save(*args, **kwargs)


class PostReaction(models.Model):
    created = models.DateTimeField(editable=False)
    reactor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    emoji = models.ForeignKey(Emoji, on_delete=models.CASCADE, related_name='reactions')

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(PostReaction, self).save(*args, **kwargs)
