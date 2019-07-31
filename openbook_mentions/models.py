from django.db import models

# Create your models here.
from openbook_auth.models import User
from openbook_posts.models import Post, PostComment


class PostUserMention(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_mentions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_mentions')


class PostCommentUserMention(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_mentions')
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='user_mentions')
