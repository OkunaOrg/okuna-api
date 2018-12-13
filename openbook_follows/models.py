from django.db import models

# Create your models here.
from openbook_auth.models import User


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follows')
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', null=False)

    class Meta:
        unique_together = ('user', 'followed_user',)

    @classmethod
    def create_follow(cls, user_id, followed_user_id, lists_ids=None):
        follow = Follow.objects.create(user_id=user_id, followed_user_id=followed_user_id)

        if lists_ids:
            follow.lists.add(*lists_ids)

        return follow
