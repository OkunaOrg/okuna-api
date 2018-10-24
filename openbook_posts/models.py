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


def get_connection_model():
    return apps.get_model('openbook_connections.Connection')


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
    def get_posts_for_user(cls, user, lists_ids=None, circles_ids=None):
        # TODO Desperately optimize. Basically the core functionality of everything.
        posts_queryset = user.posts.all()

        follows = None

        if lists_ids is not None:
            follows = user.follows.filter(list_id=lists_ids).get()
        else:
            follows = user.follows.all()

        for follow in follows:
            followed_user = follow.followed_user
            # Add the followed user public posts
            posts_queryset = posts_queryset | followed_user.world_circle.posts.all()

            is_connected_with_followed_user = None

            if circles_ids is not None:
                is_connected_with_followed_user = user.is_connected_with_user_in_circle(followed_user, circles_ids)
            else:
                is_connected_with_followed_user = user.is_connected_with_user(followed_user)

            if is_connected_with_followed_user:
                Connection = get_connection_model()

                connection = Connection.objects.select_related(
                    'target_connection__user'
                ).prefetch_related(
                    'target_connection__user__connections_circle__posts'
                ).filter(
                    user_id=user.pk,
                    target_connection__user_id=followed_user.pk).get()

                target_connection = connection.target_connection

                # Add the connected user posts with connections circle
                posts_queryset = posts_queryset | target_connection.user.connections_circle.posts.all()

                # Add the connected user circle posts we migt be in
                target_connection_circle = connection.target_connection.circle
                # The other user might not have the user in a circle yet
                if target_connection_circle:
                    target_connection_circle_posts = target_connection_circle.posts.all()
                    posts_queryset = posts_queryset | target_connection_circle_posts

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
