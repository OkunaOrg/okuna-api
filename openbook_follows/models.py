from django.db import models

# Create your models here.
from openbook_auth.models import User

from openbook_lists.models import List


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='follows', null=True)
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', null=True)

    @classmethod
    def create_follow(cls, user, followed_user, list):
        follow = cls.objects.create(user=user, followed_user=followed_user, list=list)
        return follow

    @classmethod
    def follow_exists(cls, user_a, user_b):
        count = user_a.following.filter(followed_user=user_b).count()

        if count > 0:
            return True

        return False

    @classmethod
    def follow_with_id_exists_for_user(cls, follow_id, user):
        count = user.following.filter(pk=follow_id).count()

        if count > 0:
            return True

        return False
